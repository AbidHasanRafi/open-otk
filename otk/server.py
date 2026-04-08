"""
FastAPI REST API server exposing all OTK capabilities.

Provides endpoints for generation, chat, RAG, pipelines, evaluation,
structured output, and model management with WebSocket streaming,
session management, CORS, and token-bucket rate limiting.

Start with:
    python -m otk.server          # or
    uvicorn otk.server:app --reload
"""

import time
import uuid
import asyncio
import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
    _HAS_FASTAPI = True
except ImportError:
    _HAS_FASTAPI = False

if _HAS_FASTAPI:
    # ------------------------------------------------------------------
    # Pydantic request / response models
    # ------------------------------------------------------------------

    class GenerateRequest(BaseModel):
        model: Optional[str] = None
        prompt: str
        system: Optional[str] = None
        temperature: float = 0.7
        max_tokens: Optional[int] = None

    class ChatMessage(BaseModel):
        role: str
        content: str

    class ChatRequest(BaseModel):
        model: str
        messages: List[ChatMessage]
        session_id: Optional[str] = None
        temperature: float = 0.7

    class RAGIngestRequest(BaseModel):
        documents: List[Dict[str, Any]]
        llm_model: str = "mistral"
        embedding_model: Optional[str] = None

    class RAGQueryRequest(BaseModel):
        question: str
        top_k: int = 5
        metadata_filter: Optional[Dict[str, Any]] = None

    class StructuredRequest(BaseModel):
        model: str
        prompt: str
        schema_def: Dict[str, str] = Field(..., alias="schema")
        system: Optional[str] = None

    class EvalRequest(BaseModel):
        judge_model: str
        dimensions: List[str] = ["coherence", "relevance"]
        dataset: List[Dict[str, str]]

    # ------------------------------------------------------------------
    # Rate limiter (token bucket)
    # ------------------------------------------------------------------

    class _TokenBucket:
        def __init__(self, rate: float = 10.0, capacity: float = 20.0):
            self.rate = rate
            self.capacity = capacity
            self._tokens = capacity
            self._last = time.monotonic()

        def allow(self) -> bool:
            now = time.monotonic()
            elapsed = now - self._last
            self._last = now
            self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
            if self._tokens >= 1:
                self._tokens -= 1
                return True
            return False

    # ------------------------------------------------------------------
    # App factory
    # ------------------------------------------------------------------

    def create_app(
        rate_limit_rps: float = 10.0,
        cors_origins: Optional[List[str]] = None,
    ) -> FastAPI:
        app = FastAPI(
            title="Open OTK API",
            description="REST API for the Open Ollama Toolkit",
            version="2.0.0",
        )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins or ["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        bucket = _TokenBucket(rate=rate_limit_rps, capacity=rate_limit_rps * 2)
        sessions: Dict[str, Any] = {}
        rag_instances: Dict[str, Any] = {}

        @app.middleware("http")
        async def _rate_limit(request: Request, call_next):
            if not bucket.allow():
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                )
            return await call_next(request)

        # ==============================================================
        # Health
        # ==============================================================

        @app.get("/v1/health")
        async def health():
            from .client import OllamaClient
            c = OllamaClient()
            return {"status": "ok", "ollama_running": c.is_running()}

        # ==============================================================
        # Models
        # ==============================================================

        @app.get("/v1/models")
        async def list_models():
            from .client import OllamaClient
            c = OllamaClient()
            return {"models": c.list_models()}

        # ==============================================================
        # Generate (with optional routing)
        # ==============================================================

        @app.post("/v1/generate")
        async def generate(req: GenerateRequest):
            from .client import OllamaClient
            client = OllamaClient()

            if req.model:
                resp = client.generate_with_metadata(
                    req.model, req.prompt,
                    system=req.system, temperature=req.temperature,
                    max_tokens=req.max_tokens,
                )
                return {
                    "model": req.model,
                    "response": resp.get("response", ""),
                    "eval_count": resp.get("eval_count"),
                    "eval_duration": resp.get("eval_duration"),
                }
            else:
                from .router import ModelRouter
                router = ModelRouter(client=client)
                decision = router.route(req.prompt)
                resp = client.generate_with_metadata(
                    decision.selected_model, req.prompt,
                    system=req.system, temperature=req.temperature,
                    max_tokens=req.max_tokens,
                )
                return {
                    "model": decision.selected_model,
                    "task_type": decision.task_type.value,
                    "routing_reason": decision.reason,
                    "response": resp.get("response", ""),
                    "eval_count": resp.get("eval_count"),
                }

        # ==============================================================
        # Chat with sessions
        # ==============================================================

        @app.post("/v1/chat")
        async def chat(req: ChatRequest):
            from .chat import ChatSession
            sid = req.session_id or str(uuid.uuid4())
            if sid not in sessions:
                sessions[sid] = ChatSession(req.model)
            session: Any = sessions[sid]
            msg = req.messages[-1].content if req.messages else ""
            response = session.send(msg)
            return {
                "session_id": sid,
                "response": response,
                "history_length": len(session.messages),
            }

        # ==============================================================
        # WebSocket streaming
        # ==============================================================

        @app.websocket("/v1/stream")
        async def ws_stream(ws: WebSocket):
            await ws.accept()
            from .client import OllamaClient
            client = OllamaClient()
            try:
                while True:
                    data = await ws.receive_json()
                    model = data.get("model", "mistral")
                    prompt = data.get("prompt", "")
                    for chunk in client.stream_generate(model, prompt):
                        await ws.send_json({"chunk": chunk, "done": False})
                    await ws.send_json({"chunk": "", "done": True})
            except WebSocketDisconnect:
                pass

        # ==============================================================
        # RAG
        # ==============================================================

        @app.post("/v1/rag/ingest")
        async def rag_ingest(req: RAGIngestRequest):
            from .rag import HybridRAG
            rag = HybridRAG(
                llm_model=req.llm_model,
                embedding_model=req.embedding_model,
            )
            ids = rag.add_documents(req.documents)
            key = str(uuid.uuid4())
            rag_instances[key] = rag
            return {
                "rag_id": key,
                "documents_ingested": len(ids),
                "chunks_created": rag.chunk_count,
            }

        @app.post("/v1/rag/query")
        async def rag_query(req: RAGQueryRequest, rag_id: Optional[str] = None):
            if not rag_id or rag_id not in rag_instances:
                raise HTTPException(400, "No RAG instance; ingest documents first")
            rag = rag_instances[rag_id]
            answer = rag.query(req.question, top_k=req.top_k, metadata_filter=req.metadata_filter)
            return {"answer": answer}

        # ==============================================================
        # Structured output
        # ==============================================================

        @app.post("/v1/structured")
        async def structured(req: StructuredRequest):
            from .structured import StructuredGenerator
            gen = StructuredGenerator(model=req.model)
            result = gen.generate(
                prompt=req.prompt, schema=req.schema_def, system=req.system,
            )
            return {"result": result}

        # ==============================================================
        # Evaluation
        # ==============================================================

        @app.post("/v1/evaluate")
        async def evaluate(req: EvalRequest):
            from .evaluation import EvaluationSuite, JudgeConfig
            config = JudgeConfig(
                model=req.judge_model, dimensions=req.dimensions,
            )
            suite = EvaluationSuite(judge_config=config, dataset=req.dataset)
            if any("response_a" in d for d in req.dataset):
                report = suite.run_comparative()
            else:
                report = suite.run_single()
            return report._to_dict()

        # ==============================================================
        # Metrics
        # ==============================================================

        @app.get("/v1/metrics")
        async def metrics(model: Optional[str] = None):
            from .profiler import TelemetryStore
            store = TelemetryStore()
            return store.summary(model=model)

        return app

    # Singleton for ``uvicorn otk.server:app``
    app = create_app()


def main():
    """CLI entry point for starting the server."""
    if not _HAS_FASTAPI:
        print(
            "FastAPI is required to run the OTK server.\n"
            "Install with:  pip install open-otk[server]"
        )
        return
    import uvicorn
    uvicorn.run("otk.server:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
