"""
Open Ollama Toolkit GUI - OTK v2.0

Modern sidebar-navigation interface with:
- Dashboard with live metrics
- Model browser & manager
- Integrated chat with RAG and routing
- Evaluation dashboard
- Template generator
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import subprocess
import os
import sys
import time
import re
import json
import webbrowser
import requests
from bs4 import BeautifulSoup
from otk import OllamaClient, ModelManager

# ─── Theme ────────────────────────────────────────────────────────────
COLORS = {
    "bg":            "#0d1117",
    "bg_secondary":  "#161b22",
    "bg_tertiary":   "#010409",
    "bg_card":       "#1c2128",
    "bg_hover":      "#21262d",
    "bg_input":      "#0d1117",
    "accent":        "#58a6ff",
    "accent_hover":  "#79c0ff",
    "accent_dim":    "#1f6feb",
    "accent_glow":   "#388bfd",
    "success":       "#3fb950",
    "warning":       "#d29922",
    "error":         "#f85149",
    "purple":        "#bc8cff",
    "pink":          "#f778ba",
    "text":          "#c9d1d9",
    "text_secondary":"#8b949e",
    "text_bright":   "#f0f6fc",
    "text_dim":      "#484f58",
    "border":        "#30363d",
    "border_light":  "#3d444d",
    "sidebar":       "#010409",
    "sidebar_hover": "#161b22",
    "sidebar_active": "#1f6feb",
}

FONT_TITLE    = ("Segoe UI", 20, "bold")
FONT_HEADING  = ("Segoe UI", 14, "bold")
FONT_BODY     = ("Segoe UI", 11)
FONT_SMALL    = ("Segoe UI", 10)
FONT_TINY     = ("Segoe UI", 9)
FONT_MONO     = ("Cascadia Code", 10)
FONT_ICON     = ("Segoe UI", 16)


# ─── Reusable Components ─────────────────────────────────────────────

class RoundedButton(tk.Canvas):
    """A modern flat button with hover animation."""

    def __init__(self, parent, text="", command=None, bg=None, fg=None,
                 font=None, width=140, height=38, **kw):
        bg = bg or COLORS["accent"]
        fg = fg or COLORS["text_bright"]
        font = font or FONT_SMALL
        super().__init__(parent, width=width, height=height,
                         bg=parent["bg"], highlightthickness=0, **kw)
        self._bg = bg
        self._fg = fg
        self._hover_bg = COLORS["accent_hover"] if bg == COLORS["accent"] else bg
        self._command = command
        self._rect = self.create_rectangle(0, 0, width, height, fill=bg,
                                           outline="", width=0)
        self._text = self.create_text(width // 2, height // 2, text=text,
                                      fill=fg, font=font)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _on_enter(self, _):
        self.itemconfig(self._rect, fill=self._hover_bg)
        self.config(cursor="hand2")

    def _on_leave(self, _):
        self.itemconfig(self._rect, fill=self._bg)

    def _on_click(self, _):
        if self._command:
            self._command()

    def set_text(self, text):
        self.itemconfig(self._text, text=text)

    def set_state(self, enabled=True):
        self.itemconfig(self._rect, fill=self._bg if enabled else COLORS["bg_hover"])
        self.itemconfig(self._text, fill=self._fg if enabled else COLORS["text_dim"])
        if enabled:
            self.bind("<Button-1>", self._on_click)
        else:
            self.unbind("<Button-1>")


class MetricCard(tk.Frame):
    """Dashboard metric card."""

    def __init__(self, parent, title="", value="--", accent=None, **kw):
        accent = accent or COLORS["accent"]
        super().__init__(parent, bg=COLORS["bg_card"], highlightthickness=1,
                         highlightbackground=COLORS["border"], **kw)
        self._accent = accent
        bar = tk.Frame(self, bg=accent, height=3)
        bar.pack(fill="x", side="top")
        inner = tk.Frame(self, bg=COLORS["bg_card"])
        inner.pack(fill="both", expand=True, padx=18, pady=14)
        self._title = tk.Label(inner, text=title, font=FONT_TINY,
                               bg=COLORS["bg_card"], fg=COLORS["text_secondary"])
        self._title.pack(anchor="w")
        self._value = tk.Label(inner, text=value, font=("Segoe UI", 22, "bold"),
                               bg=COLORS["bg_card"], fg=COLORS["text_bright"])
        self._value.pack(anchor="w", pady=(4, 0))

    def set_value(self, v):
        self._value.config(text=str(v))


class ThinkingIndicator(tk.Frame):
    """Animated pulsing-dots indicator shown while the LLM generates."""

    _DOTS = ("", ".", "..", "...", ".. ", ".  ")

    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg_secondary"])
        self._running = False
        self._frame = 0
        self._dot_labels = []

        inner = tk.Frame(self, bg=COLORS["bg_card"], highlightthickness=1,
                         highlightbackground=COLORS["border"])
        inner.pack(fill="x", padx=0, pady=(0, 6))

        row = tk.Frame(inner, bg=COLORS["bg_card"])
        row.pack(padx=14, pady=10)

        tk.Label(row, text="Generating", font=("Segoe UI", 10),
                 bg=COLORS["bg_card"], fg=COLORS["text_secondary"]).pack(side="left")

        for _ in range(3):
            dot = tk.Label(row, text="\u2022", font=("Segoe UI", 14, "bold"),
                           bg=COLORS["bg_card"], fg=COLORS["text_dim"])
            dot.pack(side="left", padx=1)
            self._dot_labels.append(dot)

        self._elapsed_label = tk.Label(row, text="", font=FONT_TINY,
                                       bg=COLORS["bg_card"],
                                       fg=COLORS["text_dim"])
        self._elapsed_label.pack(side="left", padx=(10, 0))

        self._start_time = 0

    def start(self):
        self._running = True
        self._frame = 0
        self._start_time = time.time()
        self._animate()

    def stop(self):
        self._running = False

    def _animate(self):
        if not self._running:
            return
        bright = COLORS["accent"]
        dim = COLORS["text_dim"]
        for i, dot in enumerate(self._dot_labels):
            dot.config(fg=bright if (self._frame % 3) == i else dim)
        self._frame += 1

        elapsed = time.time() - self._start_time
        if elapsed < 60:
            self._elapsed_label.config(text=f"{elapsed:.0f}s")
        else:
            mins = int(elapsed // 60)
            secs = int(elapsed % 60)
            self._elapsed_label.config(text=f"{mins}m {secs:02d}s")

        self.after(400, self._animate)


class Toast(tk.Toplevel):
    """Brief non-blocking notification."""

    def __init__(self, parent, message, kind="info", duration=2500):
        super().__init__(parent)
        self.overrideredirect(True)
        bg = {"info": COLORS["accent_dim"], "success": COLORS["success"],
              "error": COLORS["error"], "warning": COLORS["warning"]}.get(kind, COLORS["accent_dim"])
        self.config(bg=bg)
        tk.Label(self, text=message, bg=bg, fg=COLORS["text_bright"],
                 font=FONT_SMALL, padx=22, pady=10).pack()
        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        w = self.winfo_width()
        self.geometry(f"+{px + pw - w - 24}+{py + ph - 60}")
        self.attributes("-alpha", 0.93)
        self.after(duration, self.destroy)


# ─── Scraper (unchanged logic, trimmed) ──────────────────────────────

class OllamaModelScraper:
    def __init__(self):
        self.base_url = "https://ollama.com/search"
        self.models = []

    def scrape_models(self, max_pages=5, progress_callback=None, model_callback=None):
        self.models = []
        page = 1
        while page <= max_pages:
            if progress_callback:
                progress_callback(f"Loading models... (page {page}/{max_pages})")
            try:
                url = self.base_url if page == 1 else f"{self.base_url}?page={page}"
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                resp = requests.get(url, headers=headers, timeout=10)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                h2s = soup.find_all("h2")
                batch = [h.get_text(strip=True) for h in h2s if h.get_text(strip=True)]
                if not batch:
                    break
                self.models.extend(batch)
                if model_callback:
                    model_callback(batch, page, max_pages)
                if len(batch) < 15:
                    break
                page += 1
                time.sleep(0.5)
            except Exception as e:
                if progress_callback:
                    progress_callback(f"Error: {e}")
                break
        return self.models

    def scrape_model_tags(self, model_name):
        try:
            clean = model_name.replace("library/", "").strip()
            url = f"https://ollama.com/library/{clean}/tags"
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            tags = []
            table = soup.find("table")
            if table:
                tbody = table.find("tbody")
                rows = tbody.find_all("tr") if tbody else table.find_all("tr")
                for row in rows:
                    cols = row.find_all("td")
                    if not cols:
                        continue
                    tag = cols[0].get_text(strip=True)
                    if tag and ":" in tag and tag.lower() not in ("name", "tag", "model"):
                        tags.append(tag)
            if not tags:
                pattern = rf"{re.escape(clean)}:[\w\-.]+"
                tags = sorted(set(re.findall(pattern, soup.get_text())))
            if not tags:
                tags = [f"{clean}:latest"]
            return tags
        except Exception:
            clean = model_name.replace("library/", "").strip()
            return [f"{clean}:latest"]


# ─── Pages ────────────────────────────────────────────────────────────

class DashboardPage(tk.Frame):
    """Home dashboard with metrics and quick actions."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self._build()
        self.after(300, self.refresh)

    def _build(self):
        # Title row
        top = tk.Frame(self, bg=COLORS["bg"])
        top.pack(fill="x", padx=32, pady=(28, 8))
        tk.Label(top, text="Dashboard", font=FONT_TITLE, bg=COLORS["bg"],
                 fg=COLORS["text_bright"]).pack(side="left")
        RoundedButton(top, text="Refresh", command=self.refresh,
                      width=100, height=32, font=FONT_TINY).pack(side="right")

        # Subtitle
        tk.Label(self, text="System overview and quick actions",
                 font=FONT_SMALL, bg=COLORS["bg"],
                 fg=COLORS["text_secondary"]).pack(anchor="w", padx=32, pady=(0, 18))

        # Metric cards row
        cards = tk.Frame(self, bg=COLORS["bg"])
        cards.pack(fill="x", padx=32, pady=(0, 20))
        for i in range(4):
            cards.columnconfigure(i, weight=1)

        self.card_models = MetricCard(cards, "Installed Models", "--", COLORS["accent"])
        self.card_models.grid(row=0, column=0, sticky="nsew", padx=(0, 8), ipady=4)
        self.card_ollama = MetricCard(cards, "Ollama Status", "--", COLORS["success"])
        self.card_ollama.grid(row=0, column=1, sticky="nsew", padx=8, ipady=4)
        self.card_version = MetricCard(cards, "OTK Version", "2.0.0", COLORS["purple"])
        self.card_version.grid(row=0, column=2, sticky="nsew", padx=8, ipady=4)
        self.card_features = MetricCard(cards, "Modules", "10", COLORS["pink"])
        self.card_features.grid(row=0, column=3, sticky="nsew", padx=(8, 0), ipady=4)

        # Quick actions
        qa_label = tk.Label(self, text="Quick Actions", font=FONT_HEADING,
                            bg=COLORS["bg"], fg=COLORS["text_bright"])
        qa_label.pack(anchor="w", padx=32, pady=(10, 12))

        qa_row = tk.Frame(self, bg=COLORS["bg"])
        qa_row.pack(fill="x", padx=32, pady=(0, 18))

        actions = [
            ("Open Chat", COLORS["accent"], lambda: self.app.navigate("chat")),
            ("Browse Models", COLORS["accent_dim"], lambda: self.app.navigate("browse")),
            ("Manage Models", COLORS["success"], lambda: self.app.navigate("manage")),
            ("Evaluation Lab", COLORS["purple"], lambda: self.app.navigate("evaluate")),
        ]
        for text, color, cmd in actions:
            RoundedButton(qa_row, text=text, command=cmd, bg=color,
                          width=170, height=40, font=FONT_SMALL).pack(side="left", padx=(0, 10))

        # Recent activity / info section
        info_frame = tk.Frame(self, bg=COLORS["bg_card"], highlightthickness=1,
                              highlightbackground=COLORS["border"])
        info_frame.pack(fill="both", expand=True, padx=32, pady=(0, 28))

        inner = tk.Frame(info_frame, bg=COLORS["bg_card"])
        inner.pack(fill="both", expand=True, padx=24, pady=20)

        tk.Label(inner, text="Available Capabilities", font=FONT_HEADING,
                 bg=COLORS["bg_card"], fg=COLORS["text_bright"]).pack(anchor="w", pady=(0, 12))

        features = [
            ("Pipeline Engine", "DAG-based multi-model workflow composition with parallel execution"),
            ("Hybrid RAG", "BM25 + HNSW dense retrieval with Reciprocal Rank Fusion and LLM reranking"),
            ("LLM-as-Judge", "Automated evaluation with statistical significance testing (t-test, CI, Cohen's d)"),
            ("Model Router", "Epsilon-greedy task-aware routing with performance learning"),
            ("Structured Output", "JSON schema validation with auto-retry and self-correction"),
            ("REST API", "FastAPI server with WebSocket streaming, sessions, and rate limiting"),
            ("Profiler", "Tokens/sec, TTFT, CPU/RAM/GPU tracking with SQLite telemetry"),
        ]
        for name, desc in features:
            row = tk.Frame(inner, bg=COLORS["bg_card"])
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"  {name}", font=("Segoe UI", 10, "bold"),
                     bg=COLORS["bg_card"], fg=COLORS["accent"], width=20,
                     anchor="w").pack(side="left")
            tk.Label(row, text=desc, font=FONT_TINY, bg=COLORS["bg_card"],
                     fg=COLORS["text_secondary"], anchor="w").pack(side="left", padx=(8, 0))

    def refresh(self):
        try:
            client = OllamaClient()
            running = client.is_running()
            self.card_ollama.set_value("Online" if running else "Offline")
            if running:
                models = client.list_models()
                self.card_models.set_value(str(len(models)))
            else:
                self.card_models.set_value("--")
        except Exception:
            self.card_ollama.set_value("Offline")
            self.card_models.set_value("--")



class ChatPage(tk.Frame):
    """Chat interface with model selector and RAG toggle."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.client = OllamaClient()
        self.manager = ModelManager()
        self.session = None
        self._build()
        self.after(200, self._refresh_models)

    def _build(self):
        # Header bar
        top = tk.Frame(self, bg=COLORS["bg_secondary"])
        top.pack(fill="x")
        inner_top = tk.Frame(top, bg=COLORS["bg_secondary"])
        inner_top.pack(fill="x", padx=24, pady=12)

        tk.Label(inner_top, text="Chat", font=FONT_HEADING,
                 bg=COLORS["bg_secondary"], fg=COLORS["text_bright"]).pack(side="left")

        # Model selector
        right = tk.Frame(inner_top, bg=COLORS["bg_secondary"])
        right.pack(side="right")

        tk.Label(right, text="Model:", font=FONT_TINY, bg=COLORS["bg_secondary"],
                 fg=COLORS["text_secondary"]).pack(side="left", padx=(0, 6))
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(right, textvariable=self.model_var,
                                        font=FONT_TINY, state="readonly", width=22)
        self.model_combo.pack(side="left", padx=(0, 14))
        self.model_combo.bind("<<ComboboxSelected>>", lambda _: self._switch_model())

        self.use_router_var = tk.BooleanVar(value=False)
        tk.Checkbutton(right, text="Auto-route", variable=self.use_router_var,
                       bg=COLORS["bg_secondary"], fg=COLORS["text"],
                       selectcolor=COLORS["bg"], activebackground=COLORS["bg_secondary"],
                       font=FONT_TINY).pack(side="left")

        # Chat display
        chat_container = tk.Frame(self, bg=COLORS["bg"])
        chat_container.pack(fill="both", expand=True, padx=24, pady=(12, 0))

        self.chat_display = scrolledtext.ScrolledText(
            chat_container, wrap=tk.WORD, bg=COLORS["bg_secondary"],
            fg=COLORS["text"], font=FONT_BODY, borderwidth=0,
            highlightthickness=1, highlightbackground=COLORS["border"],
            highlightcolor=COLORS["accent_dim"], insertbackground=COLORS["accent"],
            selectbackground=COLORS["accent_dim"], padx=18, pady=16)
        self.chat_display.pack(fill="both", expand=True)
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.tag_config("user_label", foreground=COLORS["accent"],
                                     font=("Segoe UI", 10, "bold"))
        self.chat_display.tag_config("bot_label", foreground=COLORS["success"],
                                     font=("Segoe UI", 10, "bold"))
        self.chat_display.tag_config("dim", foreground=COLORS["text_secondary"],
                                     font=FONT_TINY)

        # Thinking indicator (hidden by default)
        self._thinking = ThinkingIndicator(chat_container)

        # Input bar
        input_bar = tk.Frame(self, bg=COLORS["bg_secondary"], highlightthickness=1,
                             highlightbackground=COLORS["border"])
        input_bar.pack(fill="x", padx=24, pady=(8, 20))

        self.input_box = tk.Entry(
            input_bar, font=FONT_BODY, bg=COLORS["bg_secondary"],
            fg=COLORS["text"], borderwidth=0, insertbackground=COLORS["accent"])
        self.input_box.pack(side="left", fill="both", expand=True, padx=16, pady=12, ipady=4)
        self.input_box.bind("<Return>", lambda _: self._send())

        btn_frame = tk.Frame(input_bar, bg=COLORS["bg_secondary"])
        btn_frame.pack(side="right", padx=10, pady=6)
        self.send_btn = RoundedButton(btn_frame, text="Send", command=self._send,
                                      width=80, height=32, font=FONT_TINY)
        self.send_btn.pack(side="left", padx=(0, 4))
        RoundedButton(btn_frame, text="Clear", command=self._clear,
                      bg=COLORS["bg_hover"], width=70, height=32,
                      font=FONT_TINY).pack(side="left")

    def _refresh_models(self):
        try:
            models = self.manager.list_models()
            names = [m["name"] for m in models]
            self.model_combo["values"] = names
            if names:
                self.model_combo.current(0)
                self._switch_model()
        except Exception:
            pass

    def _switch_model(self):
        from otk import ChatSession
        model = self.model_var.get()
        if model:
            self.session = ChatSession(model, system_message="You are a helpful assistant.")

    def _append(self, label, tag, text):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{label}\n", tag)
        self.chat_display.insert(tk.END, f"{text}\n\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def _show_thinking(self):
        self._thinking.pack(fill="x", before=self.chat_display, pady=(0, 4))
        self._thinking.start()
        self.chat_display.see(tk.END)

    def _hide_thinking(self):
        self._thinking.stop()
        self._thinking.pack_forget()

    def _send(self):
        msg = self.input_box.get().strip()
        if not msg:
            return
        self.input_box.delete(0, tk.END)
        self._append("You", "user_label", msg)
        self.send_btn.set_state(False)
        self.input_box.config(state=tk.DISABLED)
        self._show_thinking()

        def _worker():
            try:
                if self.use_router_var.get():
                    from otk.router import ModelRouter
                    router = ModelRouter(client=self.client)
                    decision = router.route(msg)
                    response = self.client.generate(decision.selected_model, msg)
                    self.after(0, lambda: self._append(
                        f"Assistant  ({decision.selected_model})", "bot_label", response))
                else:
                    if not self.session:
                        self._switch_model()
                    if self.session:
                        response = self.session.send(msg)
                        self.after(0, lambda: self._append("Assistant", "bot_label", response))
            except Exception as e:
                self.after(0, lambda: self._append("Error", "dim", str(e)))
            finally:
                self.after(0, self._hide_thinking)
                self.after(0, lambda: self.send_btn.set_state(True))
                self.after(0, lambda: self.input_box.config(state=tk.NORMAL))
                self.after(0, lambda: self.input_box.focus())

        threading.Thread(target=_worker, daemon=True).start()

    def _clear(self):
        if self.session:
            self.session.clear_history()
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state=tk.DISABLED)


class BrowseModelsPage(tk.Frame):
    """Browse available models from ollama.com."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.scraper = OllamaModelScraper()
        self.all_models = []
        self.current_tags = []
        self.current_model = None
        self._build()
        self.after(500, self.refresh)

    def _build(self):
        top = tk.Frame(self, bg=COLORS["bg"])
        top.pack(fill="x", padx=32, pady=(24, 6))
        tk.Label(top, text="Browse Models", font=FONT_TITLE, bg=COLORS["bg"],
                 fg=COLORS["text_bright"]).pack(side="left")
        RoundedButton(top, text="Refresh", command=self.refresh,
                      width=100, height=32, font=FONT_TINY).pack(side="right")

        tk.Label(self, text="Discover and install models from ollama.com",
                 font=FONT_SMALL, bg=COLORS["bg"],
                 fg=COLORS["text_secondary"]).pack(anchor="w", padx=32, pady=(0, 12))

        # Search
        search_bar = tk.Frame(self, bg=COLORS["bg"])
        search_bar.pack(fill="x", padx=32, pady=(0, 10))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter())
        se = tk.Entry(search_bar, textvariable=self.search_var, font=FONT_BODY,
                      bg=COLORS["bg_input"], fg=COLORS["text"],
                      insertbackground=COLORS["accent"], relief="flat",
                      highlightthickness=1, highlightbackground=COLORS["border"],
                      highlightcolor=COLORS["accent"])
        se.pack(fill="x", ipady=8)

        # Split panes
        panes = tk.Frame(self, bg=COLORS["bg"])
        panes.pack(fill="both", expand=True, padx=32, pady=(0, 10))

        # Left – model names
        left = tk.Frame(panes, bg=COLORS["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        tk.Label(left, text="Model Families", font=FONT_SMALL, bg=COLORS["bg"],
                 fg=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 4))
        ls = tk.Scrollbar(left)
        ls.pack(side="right", fill="y")
        self.names_lb = tk.Listbox(left, font=FONT_MONO, bg=COLORS["bg_secondary"],
                                   fg=COLORS["text"], selectbackground=COLORS["accent"],
                                   selectforeground=COLORS["text_bright"], relief="flat",
                                   highlightthickness=1, highlightbackground=COLORS["border"],
                                   highlightcolor=COLORS["accent"], activestyle="none",
                                   yscrollcommand=ls.set)
        self.names_lb.pack(side="left", fill="both", expand=True)
        ls.config(command=self.names_lb.yview)
        self.names_lb.bind("<<ListboxSelect>>", self._on_select)

        # Right – tags
        right = tk.Frame(panes, bg=COLORS["bg"])
        right.pack(side="right", fill="both", expand=True, padx=(8, 0))
        tag_top = tk.Frame(right, bg=COLORS["bg"])
        tag_top.pack(fill="x", pady=(0, 4))
        tk.Label(tag_top, text="Available Variants", font=FONT_SMALL,
                 bg=COLORS["bg"], fg=COLORS["text_secondary"]).pack(side="left")
        self.see_more_btn = tk.Label(tag_top, text="See on ollama.com", font=FONT_TINY,
                                     bg=COLORS["bg"], fg=COLORS["accent"], cursor="hand2")
        self.see_more_btn.pack(side="right")
        self.see_more_btn.bind("<Button-1>", lambda _: self._open_tags_page())

        rs = tk.Scrollbar(right)
        rs.pack(side="right", fill="y")
        self.tags_lb = tk.Listbox(right, font=FONT_MONO, bg=COLORS["bg_secondary"],
                                  fg=COLORS["text"], selectbackground=COLORS["accent"],
                                  selectforeground=COLORS["text_bright"], relief="flat",
                                  highlightthickness=1, highlightbackground=COLORS["border"],
                                  highlightcolor=COLORS["accent"], activestyle="none",
                                  yscrollcommand=rs.set)
        self.tags_lb.pack(side="left", fill="both", expand=True)
        rs.config(command=self.tags_lb.yview)

        # Install button
        bot = tk.Frame(self, bg=COLORS["bg"])
        bot.pack(fill="x", padx=32, pady=(4, 20))
        RoundedButton(bot, text="Install Selected", command=self._install,
                      bg=COLORS["success"], width=180, height=40).pack(side="left")
        self.status = tk.Label(bot, text="", font=FONT_TINY, bg=COLORS["bg"],
                               fg=COLORS["text_secondary"])
        self.status.pack(side="left", padx=16)

    def refresh(self):
        self.names_lb.delete(0, tk.END)
        self.all_models = []
        self.status.config(text="Loading...")

        def _work():
            def cb(batch, p, mx):
                self.after(0, lambda: self._add_batch(batch, p, mx))
            self.scraper.scrape_models(max_pages=5, model_callback=cb)
            self.after(0, self._finalize)

        threading.Thread(target=_work, daemon=True).start()

    def _add_batch(self, batch, page, mx):
        for m in batch:
            if m not in self.all_models:
                self.all_models.append(m)
                self.names_lb.insert(tk.END, f"  {m}")
        self.status.config(text=f"Loaded {len(self.all_models)} models...")

    def _finalize(self):
        self.all_models = sorted(set(self.all_models))
        self.names_lb.delete(0, tk.END)
        for m in self.all_models:
            self.names_lb.insert(tk.END, f"  {m}")
        self.status.config(text=f"{len(self.all_models)} models available", fg=COLORS["success"])

    def _filter(self):
        term = self.search_var.get().lower()
        self.names_lb.delete(0, tk.END)
        for m in self.all_models:
            if term in m.lower():
                self.names_lb.insert(tk.END, f"  {m}")

    def _on_select(self, _):
        sel = self.names_lb.curselection()
        if not sel:
            return
        name = self.names_lb.get(sel[0]).strip()
        self.current_model = name
        self.tags_lb.delete(0, tk.END)
        self.tags_lb.insert(tk.END, "  Loading...")
        self.current_tags = []

        def _work():
            tags = self.scraper.scrape_model_tags(name)
            self.after(0, lambda: self._show_tags(tags))

        threading.Thread(target=_work, daemon=True).start()

    def _show_tags(self, tags):
        self.tags_lb.delete(0, tk.END)
        self.current_tags = tags
        for t in tags:
            self.tags_lb.insert(tk.END, f"  {t}")
        self.status.config(text=f"{len(tags)} variants for {self.current_model}")

    def _open_tags_page(self):
        if self.current_model:
            clean = self.current_model.replace("library/", "").strip()
            webbrowser.open(f"https://ollama.com/library/{clean}/tags")

    def _install(self):
        sel = self.tags_lb.curselection()
        if not sel or not self.current_tags:
            Toast(self.app.root, "Select a model variant first", "warning")
            return
        idx = sel[0]
        if idx >= len(self.current_tags):
            return
        tag = self.current_tags[idx]
        if messagebox.askyesno("Install Model", f"Install '{tag}'?"):
            self.app.run_command(f"ollama pull {tag}", f"Installing {tag}")


class ManageModelsPage(tk.Frame):
    """Manage installed models."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.manager = ModelManager()
        self._build()
        self.after(200, self.refresh)

    def _build(self):
        top = tk.Frame(self, bg=COLORS["bg"])
        top.pack(fill="x", padx=32, pady=(24, 6))
        tk.Label(top, text="Manage Models", font=FONT_TITLE, bg=COLORS["bg"],
                 fg=COLORS["text_bright"]).pack(side="left")
        RoundedButton(top, text="Refresh", command=self.refresh,
                      width=100, height=32, font=FONT_TINY).pack(side="right")

        tk.Label(self, text="View, run, and delete locally installed models",
                 font=FONT_SMALL, bg=COLORS["bg"],
                 fg=COLORS["text_secondary"]).pack(anchor="w", padx=32, pady=(0, 14))

        # Tree
        tree_frame = tk.Frame(self, bg=COLORS["bg"])
        tree_frame.pack(fill="both", expand=True, padx=32)

        cols = ("Name", "Size", "Modified")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=18)
        for c in cols:
            self.tree.heading(c, text=c)
        self.tree.column("Name", width=340)
        self.tree.column("Size", width=120)
        self.tree.column("Modified", width=220)
        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Actions
        actions = tk.Frame(self, bg=COLORS["bg"])
        actions.pack(fill="x", padx=32, pady=18)
        for text, color, cmd in [
            ("Run in Terminal", COLORS["success"], self._run),
            ("Show Info", COLORS["accent_dim"], self._info),
            ("Delete", COLORS["error"], self._delete),
        ]:
            RoundedButton(actions, text=text, command=cmd, bg=color,
                          width=150, height=38).pack(side="left", padx=(0, 8))

        self.status = tk.Label(self, text="", font=FONT_TINY, bg=COLORS["bg"],
                               fg=COLORS["text_secondary"])
        self.status.pack(anchor="w", padx=32, pady=(0, 16))

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        try:
            models = self.manager.list_models()
            for m in models:
                self.tree.insert("", tk.END, values=(
                    m["name"], m["size"], m.get("modified", "N/A")))
            self.status.config(text=f"{len(models)} models installed", fg=COLORS["success"])
        except Exception as e:
            self.status.config(text=f"Error: {e}", fg=COLORS["error"])

    def _selected(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return self.tree.item(sel[0])["values"][0]

    def _run(self):
        m = self._selected()
        if not m:
            return Toast(self.app.root, "Select a model first", "warning")
        if os.name == "nt":
            subprocess.Popen(["start", "cmd", "/k", f"ollama run {m}"], shell=True)
        else:
            subprocess.Popen(["x-terminal-emulator", "-e", f"ollama run {m}"])
        Toast(self.app.root, f"Launched {m}", "success")

    def _info(self):
        m = self._selected()
        if not m:
            return Toast(self.app.root, "Select a model first", "warning")
        self.app.run_command(f"ollama show {m}", f"Model Info: {m}")

    def _delete(self):
        m = self._selected()
        if not m:
            return Toast(self.app.root, "Select a model first", "warning")
        if messagebox.askyesno("Delete", f"Delete '{m}'? This cannot be undone."):
            self.app.run_command(f"ollama rm {m}", f"Deleting {m}")
            self.after(2000, self.refresh)


class EvaluationPage(tk.Frame):
    """Full-featured evaluation dashboard with multiple test modes."""

    _DIMENSIONS = ["coherence", "relevance", "factuality", "helpfulness", "safety", "creativity"]

    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self._all_model_names = []
        self._running = False
        self._build()
        self.after(300, self._refresh_models)

    # ── Layout ────────────────────────────────────────────────────────

    def _build(self):
        top = tk.Frame(self, bg=COLORS["bg"])
        top.pack(fill="x", padx=32, pady=(24, 6))
        tk.Label(top, text="Evaluation Lab", font=FONT_TITLE, bg=COLORS["bg"],
                 fg=COLORS["text_bright"]).pack(side="left")
        RoundedButton(top, text="Refresh Models", command=self._refresh_models,
                      width=140, height=30, font=FONT_TINY).pack(side="right")
        tk.Label(self, text="Select models, choose an evaluation mode, and run",
                 font=FONT_SMALL, bg=COLORS["bg"],
                 fg=COLORS["text_secondary"]).pack(anchor="w", padx=32, pady=(0, 12))

        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=32, pady=(0, 20))

        # ── Left: model picker + config ───────────────────────────────
        left = tk.Frame(body, bg=COLORS["bg_card"], width=310, highlightthickness=1,
                        highlightbackground=COLORS["border"])
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        linner = tk.Frame(left, bg=COLORS["bg_card"])
        linner.pack(fill="both", expand=True, padx=14, pady=14)

        # Model multi-select
        tk.Label(linner, text="Models to Evaluate", font=("Segoe UI", 10, "bold"),
                 bg=COLORS["bg_card"], fg=COLORS["text"]).pack(anchor="w")
        tk.Label(linner, text="Ctrl+click to select multiple", font=FONT_TINY,
                 bg=COLORS["bg_card"], fg=COLORS["text_dim"]).pack(anchor="w", pady=(0, 4))

        mlf = tk.Frame(linner, bg=COLORS["bg_card"])
        mlf.pack(fill="both", expand=True, pady=(0, 8))
        ms = tk.Scrollbar(mlf)
        ms.pack(side="right", fill="y")
        self.model_lb = tk.Listbox(
            mlf, font=FONT_MONO, selectmode=tk.EXTENDED,
            bg=COLORS["bg_input"], fg=COLORS["text"],
            selectbackground=COLORS["accent"], selectforeground=COLORS["text_bright"],
            relief="flat", highlightthickness=1, highlightbackground=COLORS["border"],
            highlightcolor=COLORS["accent"], activestyle="none", exportselection=False,
            yscrollcommand=ms.set)
        self.model_lb.pack(side="left", fill="both", expand=True)
        ms.config(command=self.model_lb.yview)

        sel_btns = tk.Frame(linner, bg=COLORS["bg_card"])
        sel_btns.pack(fill="x", pady=(0, 10))
        for txt, cmd in [("Select All", self._select_all), ("Clear", self._clear_sel)]:
            b = tk.Label(sel_btns, text=txt, font=FONT_TINY, bg=COLORS["bg_card"],
                         fg=COLORS["accent"], cursor="hand2")
            b.pack(side="left", padx=(0, 12))
            b.bind("<Button-1>", lambda _, c=cmd: c())

        sep = tk.Frame(linner, bg=COLORS["border"], height=1)
        sep.pack(fill="x", pady=(0, 10))

        # Judge model
        tk.Label(linner, text="Judge Model", font=("Segoe UI", 10, "bold"),
                 bg=COLORS["bg_card"], fg=COLORS["text"]).pack(anchor="w")
        tk.Label(linner, text="Used for quality scoring", font=FONT_TINY,
                 bg=COLORS["bg_card"], fg=COLORS["text_dim"]).pack(anchor="w", pady=(0, 4))
        self.judge_var = tk.StringVar()
        self.judge_combo = ttk.Combobox(linner, textvariable=self.judge_var,
                                        font=FONT_TINY, state="readonly", width=28)
        self.judge_combo.pack(anchor="w", pady=(0, 10))

        sep2 = tk.Frame(linner, bg=COLORS["border"], height=1)
        sep2.pack(fill="x", pady=(0, 10))

        # Options
        tk.Label(linner, text="Options", font=("Segoe UI", 10, "bold"),
                 bg=COLORS["bg_card"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 4))

        opt = tk.Frame(linner, bg=COLORS["bg_card"])
        opt.pack(fill="x", pady=(0, 4))
        tk.Label(opt, text="Iterations:", font=FONT_TINY,
                 bg=COLORS["bg_card"], fg=COLORS["text_secondary"]).pack(side="left")
        self.iter_var = tk.IntVar(value=3)
        tk.Spinbox(opt, from_=1, to=20, width=4, textvariable=self.iter_var,
                   font=FONT_TINY, bg=COLORS["bg_input"], fg=COLORS["text"],
                   buttonbackground=COLORS["bg_hover"], relief="flat",
                   highlightthickness=1, highlightbackground=COLORS["border"]).pack(side="right")

        opt2 = tk.Frame(linner, bg=COLORS["bg_card"])
        opt2.pack(fill="x", pady=(0, 4))
        tk.Label(opt2, text="Temperature:", font=FONT_TINY,
                 bg=COLORS["bg_card"], fg=COLORS["text_secondary"]).pack(side="left")
        self.temp_var = tk.DoubleVar(value=0.7)
        tk.Spinbox(opt2, from_=0.0, to=2.0, increment=0.1, width=4,
                   textvariable=self.temp_var, font=FONT_TINY,
                   bg=COLORS["bg_input"], fg=COLORS["text"],
                   buttonbackground=COLORS["bg_hover"], relief="flat",
                   highlightthickness=1, highlightbackground=COLORS["border"]).pack(side="right")

        # Quality dimensions checkboxes
        sep3 = tk.Frame(linner, bg=COLORS["border"], height=1)
        sep3.pack(fill="x", pady=(8, 8))
        tk.Label(linner, text="Quality Dimensions", font=("Segoe UI", 10, "bold"),
                 bg=COLORS["bg_card"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 4))
        self.dim_vars = {}
        for dim in self._DIMENSIONS:
            v = tk.BooleanVar(value=dim in ("coherence", "relevance", "helpfulness"))
            self.dim_vars[dim] = v
            tk.Checkbutton(linner, text=dim.capitalize(), variable=v,
                           bg=COLORS["bg_card"], fg=COLORS["text"],
                           selectcolor=COLORS["bg_input"],
                           activebackground=COLORS["bg_card"],
                           font=FONT_TINY).pack(anchor="w")

        # ── Right: mode tabs + prompt + results ───────────────────────
        right = tk.Frame(body, bg=COLORS["bg"])
        right.pack(side="left", fill="both", expand=True)

        # Prompt
        pf = tk.Frame(right, bg=COLORS["bg_card"], highlightthickness=1,
                      highlightbackground=COLORS["border"])
        pf.pack(fill="x", pady=(0, 8))
        pinner = tk.Frame(pf, bg=COLORS["bg_card"])
        pinner.pack(fill="x", padx=14, pady=10)
        tk.Label(pinner, text="Prompt:", font=("Segoe UI", 10, "bold"),
                 bg=COLORS["bg_card"], fg=COLORS["text"]).pack(anchor="w")
        self.prompt_text = tk.Text(pinner, font=FONT_BODY, bg=COLORS["bg_input"],
                                   fg=COLORS["text"], insertbackground=COLORS["accent"],
                                   relief="flat", highlightthickness=1,
                                   highlightbackground=COLORS["border"],
                                   highlightcolor=COLORS["accent"], height=3, wrap=tk.WORD)
        self.prompt_text.pack(fill="x", pady=(4, 0))
        self.prompt_text.insert("1.0", "Explain the theory of relativity in simple terms.")

        # Mode selector row
        mode_row = tk.Frame(right, bg=COLORS["bg"])
        mode_row.pack(fill="x", pady=(0, 8))
        self._mode_var = tk.StringVar(value="benchmark")
        self._mode_btns = {}
        modes = [
            ("benchmark", "Speed Benchmark"),
            ("compare",   "Model Comparison"),
            ("quality",   "Quality Evaluation"),
            ("ab_test",   "A/B Test"),
        ]
        for key, label in modes:
            b = tk.Label(mode_row, text=label, font=FONT_TINY, padx=14, pady=6,
                         cursor="hand2", bg=COLORS["bg_card"], fg=COLORS["text_secondary"])
            b.pack(side="left", padx=(0, 4))
            b.bind("<Button-1>", lambda _, k=key: self._set_mode(k))
            self._mode_btns[key] = b
        self._set_mode("benchmark")

        # Run button + thinking indicator
        run_row = tk.Frame(right, bg=COLORS["bg"])
        run_row.pack(fill="x", pady=(0, 6))
        self._run_btn = RoundedButton(run_row, text="Run Evaluation",
                                      command=self._run, bg=COLORS["accent"],
                                      width=170, height=38)
        self._run_btn.pack(side="left")
        self._thinking = ThinkingIndicator(run_row)

        # Results
        self.results_text = scrolledtext.ScrolledText(
            right, font=FONT_MONO, bg=COLORS["bg_secondary"], fg=COLORS["text"],
            highlightthickness=1, highlightbackground=COLORS["border"],
            insertbackground=COLORS["accent"], padx=16, pady=14)
        self.results_text.pack(fill="both", expand=True)
        self.results_text.tag_config("heading", foreground=COLORS["accent"],
                                     font=("Cascadia Code", 11, "bold"))
        self.results_text.tag_config("good", foreground=COLORS["success"])
        self.results_text.tag_config("warn", foreground=COLORS["warning"])
        self.results_text.tag_config("dim", foreground=COLORS["text_secondary"])
        self._show("Select models on the left, pick an evaluation mode, and click Run.\n\n"
                   "Modes:\n"
                   "  Speed Benchmark   - Latency, tokens/sec, std dev over N iterations\n"
                   "  Model Comparison  - Side-by-side output & timing comparison\n"
                   "  Quality Evaluation - LLM-as-Judge scoring on selected dimensions\n"
                   "  A/B Test          - Head-to-head pairwise comparison (pick 2 models)")

    # ── Helpers ───────────────────────────────────────────────────────

    def _set_mode(self, key):
        self._mode_var.set(key)
        for k, b in self._mode_btns.items():
            if k == key:
                b.config(bg=COLORS["accent"], fg=COLORS["text_bright"])
            else:
                b.config(bg=COLORS["bg_card"], fg=COLORS["text_secondary"])

    def _refresh_models(self):
        try:
            mgr = ModelManager()
            models = mgr.list_models()
            self._all_model_names = [m["name"] for m in models]
            self.model_lb.delete(0, tk.END)
            for n in self._all_model_names:
                self.model_lb.insert(tk.END, f"  {n}")
            self.judge_combo["values"] = self._all_model_names
            if self._all_model_names:
                self.judge_combo.current(0)
        except Exception:
            pass

    def _select_all(self):
        self.model_lb.select_set(0, tk.END)

    def _clear_sel(self):
        self.model_lb.selection_clear(0, tk.END)

    def _selected_models(self):
        return [self._all_model_names[i] for i in self.model_lb.curselection()
                if i < len(self._all_model_names)]

    def _get_prompt(self):
        return self.prompt_text.get("1.0", tk.END).strip()

    def _active_dims(self):
        return [d for d, v in self.dim_vars.items() if v.get()]

    def _show(self, text):
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert("1.0", text)
        self.results_text.config(state=tk.DISABLED)

    def _append_line(self, text, tag=""):
        self.results_text.config(state=tk.NORMAL)
        if tag:
            self.results_text.insert(tk.END, text + "\n", tag)
        else:
            self.results_text.insert(tk.END, text + "\n")
        self.results_text.see(tk.END)
        self.results_text.config(state=tk.DISABLED)

    def _start_run(self):
        self._running = True
        self._run_btn.set_state(False)
        self._thinking.pack(side="left", padx=(12, 0))
        self._thinking.start()
        self._show("")

    def _end_run(self):
        self._running = False
        self._thinking.stop()
        self._thinking.pack_forget()
        self._run_btn.set_state(True)

    # ── Dispatcher ────────────────────────────────────────────────────

    def _run(self):
        models = self._selected_models()
        prompt = self._get_prompt()
        mode = self._mode_var.get()

        if not models:
            return Toast(self.app.root, "Select at least one model", "warning")
        if not prompt:
            return Toast(self.app.root, "Enter a prompt", "warning")
        if mode == "ab_test" and len(models) != 2:
            return Toast(self.app.root, "A/B Test requires exactly 2 models", "warning")

        self._start_run()

        dispatch = {
            "benchmark": self._run_benchmark,
            "compare":   self._run_compare,
            "quality":   self._run_quality,
            "ab_test":   self._run_ab_test,
        }
        threading.Thread(target=dispatch[mode], args=(models, prompt), daemon=True).start()

    # ── Mode: Speed Benchmark ─────────────────────────────────────────

    def _run_benchmark(self, models, prompt):
        try:
            from otk.experimentation import ModelExperiment
            iters = self.iter_var.get()
            temp = self.temp_var.get()
            exp = ModelExperiment()

            self.after(0, lambda: self._append_line(
                f"Speed Benchmark  ({iters} iterations, temp={temp})", "heading"))
            self.after(0, lambda: self._append_line("=" * 64))

            all_stats = {}
            for model in models:
                self.after(0, lambda m=model: self._append_line(f"\nBenchmarking {m}...", "dim"))
                stats = exp.benchmark(model, prompt, iterations=iters, temperature=temp)
                all_stats[model] = stats
                if "error" in stats:
                    self.after(0, lambda s=stats: self._append_line(f"  ERROR: {s['error']}", "warn"))
                else:
                    lines = [
                        f"\n  Model: {stats['model']}",
                        f"  Iterations:      {stats['iterations']}",
                        f"  Avg Time:        {stats['avg_time']:.3f}s",
                        f"  Min Time:        {stats['min_time']:.3f}s",
                        f"  Max Time:        {stats['max_time']:.3f}s",
                        f"  Std Dev:         {stats['std_dev']:.3f}s",
                        f"  Avg Tokens:      {stats['avg_tokens']:.0f}",
                        f"  Tokens/sec:      {stats['tokens_per_second']:.1f}",
                    ]
                    for ln in lines:
                        self.after(0, lambda l=ln: self._append_line(l))

            # Ranking
            ranked = sorted(
                [(m, s) for m, s in all_stats.items() if "error" not in s],
                key=lambda x: x[1]["avg_time"])
            if len(ranked) > 1:
                self.after(0, lambda: self._append_line("\n" + "=" * 64))
                self.after(0, lambda: self._append_line("Ranking (fastest first)", "heading"))
                for i, (m, s) in enumerate(ranked, 1):
                    self.after(0, lambda i=i, m=m, s=s: self._append_line(
                        f"  #{i}  {m:30s}  {s['avg_time']:.3f}s  ({s['tokens_per_second']:.1f} tok/s)",
                        "good" if i == 1 else ""))

        except Exception as e:
            self.after(0, lambda: self._append_line(f"\nError: {e}", "warn"))
        finally:
            self.after(0, self._end_run)

    # ── Mode: Model Comparison ────────────────────────────────────────

    def _run_compare(self, models, prompt):
        try:
            from otk.experimentation import ModelExperiment
            exp = ModelExperiment()
            temp = self.temp_var.get()

            self.after(0, lambda: self._append_line("Model Comparison", "heading"))
            self.after(0, lambda: self._append_line("=" * 64))
            self.after(0, lambda: self._append_line(f"Prompt: {prompt[:80]}...\n", "dim"))

            results = []
            for model in models:
                self.after(0, lambda m=model: self._append_line(f"Generating with {m}...", "dim"))
                r = exp.run_single(model, prompt, temperature=temp)
                results.append(r)

                if r.error:
                    self.after(0, lambda r=r: self._append_line(
                        f"\n  {r.model}: ERROR - {r.error}", "warn"))
                else:
                    tps = r.tokens_estimated / r.time_taken if r.time_taken > 0 else 0
                    header = f"\n  {r.model}  [{r.time_taken:.2f}s | ~{r.tokens_estimated} tokens | {tps:.1f} tok/s]"
                    self.after(0, lambda h=header: self._append_line(h, "good"))
                    self.after(0, lambda: self._append_line("  " + "-" * 60))
                    resp_lines = r.response.strip().split("\n")
                    for ln in resp_lines[:20]:
                        self.after(0, lambda l=ln: self._append_line(f"  {l}"))
                    if len(resp_lines) > 20:
                        self.after(0, lambda: self._append_line(
                            f"  ... ({len(resp_lines) - 20} more lines)", "dim"))

            ok = [r for r in results if not r.error]
            if len(ok) > 1:
                fastest = min(ok, key=lambda r: r.time_taken)
                longest_resp = max(ok, key=lambda r: r.tokens_estimated)
                self.after(0, lambda: self._append_line("\n" + "=" * 64))
                self.after(0, lambda: self._append_line("Summary", "heading"))
                self.after(0, lambda: self._append_line(
                    f"  Fastest:          {fastest.model} ({fastest.time_taken:.2f}s)", "good"))
                self.after(0, lambda: self._append_line(
                    f"  Most verbose:     {longest_resp.model} (~{longest_resp.tokens_estimated} tokens)"))

        except Exception as e:
            self.after(0, lambda: self._append_line(f"\nError: {e}", "warn"))
        finally:
            self.after(0, self._end_run)

    # ── Mode: Quality Evaluation ──────────────────────────────────────

    def _run_quality(self, models, prompt):
        try:
            from otk.experimentation import ModelExperiment
            from otk.evaluation import LLMJudge, JudgeConfig

            judge_model = self.judge_var.get()
            dims = self._active_dims()
            if not judge_model:
                self.after(0, lambda: self._show("Select a judge model first."))
                return
            if not dims:
                self.after(0, lambda: self._show("Select at least one quality dimension."))
                return

            temp = self.temp_var.get()
            client = OllamaClient()
            judge = LLMJudge(JudgeConfig(model=judge_model, dimensions=dims), client=client)
            exp = ModelExperiment(client=client)

            self.after(0, lambda: self._append_line(
                f"Quality Evaluation  (judge={judge_model})", "heading"))
            self.after(0, lambda: self._append_line("=" * 64))
            self.after(0, lambda: self._append_line(
                f"Dimensions: {', '.join(d.capitalize() for d in dims)}\n", "dim"))

            all_scores = {}
            for model in models:
                self.after(0, lambda m=model: self._append_line(f"Evaluating {m}...", "dim"))
                r = exp.run_single(model, prompt, temperature=temp)
                if r.error:
                    self.after(0, lambda m=model, e=r.error: self._append_line(
                        f"\n  {m}: ERROR - {e}", "warn"))
                    continue

                scores = judge.evaluate(prompt, r.response)
                score_map = {s.dimension: s.score for s in scores}
                all_scores[model] = score_map
                avg = sum(score_map.values()) / len(score_map) if score_map else 0

                self.after(0, lambda m=model, a=avg: self._append_line(
                    f"\n  {m}  (avg: {a:.1f}/5)", "good" if a >= 3.5 else "warn"))
                for dim, sc in score_map.items():
                    bar = "#" * int(sc) + "-" * (5 - int(sc))
                    self.after(0, lambda d=dim, s=sc, b=bar: self._append_line(
                        f"    {d:14s}  [{b}]  {s:.1f}/5"))

                tps = r.tokens_estimated / r.time_taken if r.time_taken > 0 else 0
                self.after(0, lambda r=r, t=tps: self._append_line(
                    f"    time: {r.time_taken:.2f}s | tokens: ~{r.tokens_estimated} | {t:.1f} tok/s", "dim"))

            if len(all_scores) > 1:
                self.after(0, lambda: self._append_line("\n" + "=" * 64))
                self.after(0, lambda: self._append_line("Quality Ranking (by average score)", "heading"))
                ranked = sorted(all_scores.items(),
                                key=lambda x: sum(x[1].values()) / len(x[1]),
                                reverse=True)
                for i, (m, sc) in enumerate(ranked, 1):
                    avg = sum(sc.values()) / len(sc)
                    self.after(0, lambda i=i, m=m, a=avg: self._append_line(
                        f"  #{i}  {m:30s}  avg {a:.1f}/5",
                        "good" if i == 1 else ""))

        except Exception as e:
            self.after(0, lambda: self._append_line(f"\nError: {e}", "warn"))
        finally:
            self.after(0, self._end_run)

    # ── Mode: A/B Test ────────────────────────────────────────────────

    def _run_ab_test(self, models, prompt):
        try:
            from otk.evaluation import LLMJudge, JudgeConfig

            model_a, model_b = models[0], models[1]
            judge_model = self.judge_var.get()
            if not judge_model:
                self.after(0, lambda: self._show("Select a judge model first."))
                return

            client = OllamaClient()
            iters = self.iter_var.get()
            temp = self.temp_var.get()

            self.after(0, lambda: self._append_line(
                f"A/B Test: {model_a} vs {model_b}", "heading"))
            self.after(0, lambda: self._append_line("=" * 64))
            self.after(0, lambda: self._append_line(f"Judge: {judge_model} | Rounds: {iters}\n", "dim"))

            wins = {model_a: 0, model_b: 0, "tie": 0}

            for i in range(1, iters + 1):
                self.after(0, lambda i=i: self._append_line(f"Round {i}...", "dim"))
                try:
                    resp_a = client.generate(model_a, prompt, temperature=temp)
                    resp_b = client.generate(model_b, prompt, temperature=temp)

                    judge_prompt = (
                        f"You are an impartial judge. Compare these two responses to the prompt: "
                        f"\"{prompt}\"\n\n"
                        f"Response A:\n{resp_a[:500]}\n\n"
                        f"Response B:\n{resp_b[:500]}\n\n"
                        f"Which response is better overall? Reply ONLY with 'A', 'B', or 'TIE'."
                    )
                    verdict = client.generate(judge_model, judge_prompt, temperature=0.1).strip().upper()

                    if "A" in verdict and "B" not in verdict:
                        winner = model_a
                        wins[model_a] += 1
                    elif "B" in verdict and "A" not in verdict:
                        winner = model_b
                        wins[model_b] += 1
                    else:
                        winner = "Tie"
                        wins["tie"] += 1

                    self.after(0, lambda i=i, w=winner: self._append_line(
                        f"  Round {i}: Winner = {w}",
                        "good" if w != "Tie" else "dim"))
                except Exception as e:
                    self.after(0, lambda i=i, e=e: self._append_line(
                        f"  Round {i}: Error - {e}", "warn"))

            self.after(0, lambda: self._append_line("\n" + "=" * 64))
            self.after(0, lambda: self._append_line("Final Results", "heading"))
            self.after(0, lambda: self._append_line(
                f"  {model_a:30s}  {wins[model_a]} wins",
                "good" if wins[model_a] > wins[model_b] else ""))
            self.after(0, lambda: self._append_line(
                f"  {model_b:30s}  {wins[model_b]} wins",
                "good" if wins[model_b] > wins[model_a] else ""))
            self.after(0, lambda: self._append_line(f"  {'Ties':30s}  {wins['tie']}", "dim"))

            if wins[model_a] > wins[model_b]:
                self.after(0, lambda: self._append_line(f"\n  Winner: {model_a}", "good"))
            elif wins[model_b] > wins[model_a]:
                self.after(0, lambda: self._append_line(f"\n  Winner: {model_b}", "good"))
            else:
                self.after(0, lambda: self._append_line("\n  Result: Draw", "dim"))

        except Exception as e:
            self.after(0, lambda: self._append_line(f"\nError: {e}", "warn"))
        finally:
            self.after(0, self._end_run)


class TemplatePage(tk.Frame):
    """Template generator page."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.manager = ModelManager()
        self._build()
        self.after(200, self._refresh_models)

    def _build(self):
        top = tk.Frame(self, bg=COLORS["bg"])
        top.pack(fill="x", padx=32, pady=(24, 6))
        tk.Label(top, text="Template Generator", font=FONT_TITLE, bg=COLORS["bg"],
                 fg=COLORS["text_bright"]).pack(side="left")

        tk.Label(self, text="Generate production-ready starter code for your project",
                 font=FONT_SMALL, bg=COLORS["bg"],
                 fg=COLORS["text_secondary"]).pack(anchor="w", padx=32, pady=(0, 18))

        form = tk.Frame(self, bg=COLORS["bg"])
        form.pack(fill="both", expand=True, padx=32)

        # Model
        tk.Label(form, text="Model", font=FONT_SMALL, bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 4))
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(form, textvariable=self.model_var,
                                        font=FONT_BODY, state="readonly", width=30)
        self.model_combo.pack(anchor="w", pady=(0, 14))

        # Template type
        tk.Label(form, text="Template Type", font=FONT_SMALL, bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 4))

        self.templates_list = [
            ("Simple Chat", "chat"),
            ("Streaming Chat", "streaming"),
            ("Custom Model with Hooks", "custom"),
            ("Experimentation", "experiment"),
            ("Integration Service", "integration"),
            ("Desktop GUI (Tkinter)", "tkinter"),
            ("Advanced GUI (Tkinter)", "tkinter_advanced"),
        ]
        self.tmpl_var = tk.StringVar(value="chat")
        for label, val in self.templates_list:
            tk.Radiobutton(form, text=label, variable=self.tmpl_var, value=val,
                           font=FONT_SMALL, bg=COLORS["bg"], fg=COLORS["text"],
                           selectcolor=COLORS["bg_secondary"],
                           activebackground=COLORS["bg"],
                           activeforeground=COLORS["accent"]).pack(anchor="w", pady=1)

        # Filename
        tk.Label(form, text="Output Filename", font=FONT_SMALL, bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(14, 4))
        fn_row = tk.Frame(form, bg=COLORS["bg"])
        fn_row.pack(fill="x", pady=(0, 14))
        self.fn_var = tk.StringVar(value="my_otk_app.py")
        tk.Entry(fn_row, textvariable=self.fn_var, font=FONT_BODY,
                 bg=COLORS["bg_input"], fg=COLORS["text"],
                 insertbackground=COLORS["accent"], relief="flat",
                 highlightthickness=1, highlightbackground=COLORS["border"],
                 highlightcolor=COLORS["accent"]).pack(side="left", fill="x",
                                                        expand=True, ipady=6, padx=(0, 8))
        RoundedButton(fn_row, text="Browse", command=self._browse,
                      bg=COLORS["bg_hover"], width=90, height=32,
                      font=FONT_TINY).pack(side="right")

        RoundedButton(form, text="Generate Template", command=self._generate,
                      width=200, height=42).pack(anchor="w", pady=(8, 0))

        self.status = tk.Label(form, text="", font=FONT_TINY, bg=COLORS["bg"],
                               fg=COLORS["text_secondary"])
        self.status.pack(anchor="w", pady=8)

    def _refresh_models(self):
        try:
            models = self.manager.list_models()
            names = [m["name"] for m in models]
            self.model_combo["values"] = names
            if names:
                self.model_combo.current(0)
        except Exception:
            pass

    def _browse(self):
        fn = filedialog.asksaveasfilename(defaultextension=".py",
                                          filetypes=[("Python", "*.py")])
        if fn:
            self.fn_var.set(fn)

    def _generate(self):
        model = self.model_var.get()
        tmpl = self.tmpl_var.get()
        fn = self.fn_var.get()
        if not model or not fn:
            return Toast(self.app.root, "Select model and filename", "warning")
        try:
            name = next(n for n, v in self.templates_list if v == tmpl)
            create_template(model, name, tmpl, fn)
            self.status.config(text=f"Created {fn}", fg=COLORS["success"])
            Toast(self.app.root, f"Template '{fn}' created!", "success")
        except Exception as e:
            self.status.config(text=f"Error: {e}", fg=COLORS["error"])


# Keep the create_template function from the original
def create_template(model, template_name, template_type, filename):
    """Generate template files. Uses __MODEL__ placeholder to avoid f-string clashes."""

    _PLACEHOLDER = "__MODEL__"

    templates = {}

    # ── 1. Simple Chat ────────────────────────────────────────────────
    templates["chat"] = '''"""
Simple Chat - Generated with Open OTK
"""
from otk import ChatSession


def main():
    session = ChatSession(
        model="__MODEL__",
        system_message="You are a helpful assistant.",
        temperature=0.7,
    )

    print("Chat with __MODEL__")
    print("=" * 50)
    print("Commands: 'quit' to exit, 'clear' to reset history")
    print("=" * 50)

    while True:
        try:
            msg = input("\\nYou: ").strip()
            if not msg:
                continue
            if msg.lower() in ("quit", "exit"):
                print("\\nGoodbye!")
                break
            if msg.lower() == "clear":
                session.clear_history()
                print("History cleared.")
                continue

            response = session.send(msg)
            print(f"\\nAssistant: {response}")

        except KeyboardInterrupt:
            print("\\n\\nGoodbye!")
            break
        except Exception as e:
            print(f"\\nError: {e}")


if __name__ == "__main__":
    main()
'''

    # ── 2. Streaming Chat ─────────────────────────────────────────────
    templates["streaming"] = '''"""
Streaming Chat - Generated with Open OTK
"""
from otk import ChatSession


def main():
    session = ChatSession(
        model="__MODEL__",
        system_message="You are a helpful assistant.",
        temperature=0.7,
    )

    print("Streaming Chat with __MODEL__")
    print("=" * 50)
    print("Commands: 'quit' to exit, 'clear' to reset history")
    print("=" * 50)

    while True:
        try:
            msg = input("\\nYou: ").strip()
            if not msg:
                continue
            if msg.lower() in ("quit", "exit"):
                print("\\nGoodbye!")
                break
            if msg.lower() == "clear":
                session.clear_history()
                print("History cleared.")
                continue

            print("\\nAssistant: ", end="", flush=True)
            for chunk in session.send_stream(msg):
                print(chunk, end="", flush=True)
            print()

        except KeyboardInterrupt:
            print("\\n\\nGoodbye!")
            break
        except Exception as e:
            print(f"\\nError: {e}")


if __name__ == "__main__":
    main()
'''

    # ── 3. Custom Model with Hooks ────────────────────────────────────
    templates["custom"] = '''"""
Custom Model with Hooks - Generated with Open OTK
"""
from otk import ModelBuilder, HookType, HookContext


def pre_hook(ctx: HookContext):
    """Called before sending to model."""
    prompt = ctx.prompt or ""
    print(f"  [pre]  Sending {len(prompt)} chars to model...")


def post_hook(ctx: HookContext):
    """Called after receiving response."""
    text = ctx.output_text or ""
    print(f"  [post] Received {len(text)} chars from model")


def main():
    model = (
        ModelBuilder("__MODEL__")
        .with_temperature(0.8)
        .with_hook(HookType.PRE_PROCESS, pre_hook)
        .with_hook(HookType.POST_PROCESS, post_hook)
        .build()
    )

    print("Custom Model Chat with __MODEL__")
    print("=" * 50)
    print("Hooks: pre-process and post-process logging active")
    print("Commands: 'quit' to exit")
    print("=" * 50)

    while True:
        try:
            msg = input("\\nYou: ").strip()
            if not msg:
                continue
            if msg.lower() in ("quit", "exit"):
                print("\\nGoodbye!")
                break

            response = model.generate(msg)
            print(f"\\nAssistant: {response}")

        except KeyboardInterrupt:
            print("\\n\\nGoodbye!")
            break
        except Exception as e:
            print(f"\\nError: {e}")


if __name__ == "__main__":
    main()
'''

    # ── 4. Experimentation ────────────────────────────────────────────
    templates["experiment"] = '''"""
Experimentation - Generated with Open OTK
"""
from otk import ModelExperiment


def main():
    exp = ModelExperiment()

    print("Model Experimentation with __MODEL__")
    print("=" * 60)

    # Compare models (single model here, add more to the list)
    print("\\n--- Model Comparison ---")
    result = exp.compare_models(
        models=["__MODEL__"],
        prompt="Explain quantum computing in one paragraph",
    )
    exp.print_comparison(result)

    # Benchmark over multiple iterations
    print("\\n--- Speed Benchmark (5 iterations) ---")
    stats = exp.benchmark(
        "__MODEL__",
        "Write a haiku about programming",
        iterations=5,
    )
    exp.print_benchmark(stats)

    # Temperature sweep
    print("\\n--- Temperature Sweep ---")
    for temp in [0.2, 0.5, 0.8, 1.2]:
        r = exp.run_single(
            "__MODEL__",
            "Write a creative one-liner about AI",
            temperature=temp,
        )
        preview = r.response[:80].replace("\\n", " ") if not r.error else r.error
        print(f"  temp={temp:.1f}  ({r.time_taken:.2f}s)  {preview}")


if __name__ == "__main__":
    main()
'''

    # ── 5. Integration Service ────────────────────────────────────────
    templates["integration"] = '''"""
Integration Service - Generated with Open OTK

Drop-in AI service class you can import into any project.
"""
from otk import OllamaClient, ChatSession


class AIService:
    """Reusable AI service backed by a local Ollama model."""

    def __init__(self, model="__MODEL__"):
        self.client = OllamaClient()
        self.model = model
        self.session = ChatSession(model=model, temperature=0.7)

    def ask(self, question: str) -> str:
        """Ask a one-shot question (no memory)."""
        return self.client.generate(self.model, question)

    def chat(self, message: str) -> str:
        """Send a message in an ongoing conversation."""
        return self.session.send(message)

    def summarize(self, text: str) -> str:
        """Summarize a block of text."""
        prompt = "Summarize the following text concisely:\\n\\n" + text
        return self.client.generate(self.model, prompt)

    def analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of a text."""
        prompt = (
            "Analyze the sentiment of this text. "
            "Reply with: Positive, Negative, or Neutral, "
            "followed by a brief explanation.\\n\\n" + text
        )
        return self.client.generate(self.model, prompt)


def main():
    svc = AIService()

    print("AI Service Integration Demo")
    print("=" * 50)

    # One-shot question
    print("\\n--- One-shot Question ---")
    answer = svc.ask("What is Python?")
    print(f"Q: What is Python?\\nA: {answer}")

    # Conversation
    print("\\n--- Conversation ---")
    r1 = svc.chat("What are the main features of Python?")
    print(f"Turn 1: {r1[:200]}")
    r2 = svc.chat("Which one is most important for beginners?")
    print(f"Turn 2: {r2[:200]}")

    # Summarize
    print("\\n--- Summarization ---")
    text = (
        "Python is a high-level, general-purpose programming language. "
        "Its design philosophy emphasizes code readability with the use "
        "of significant indentation. Python is dynamically typed and "
        "garbage-collected. It supports multiple programming paradigms."
    )
    summary = svc.summarize(text)
    print(f"Summary: {summary}")


if __name__ == "__main__":
    main()
'''

    # ── 6. Tkinter GUI ───────────────────────────────────────────────
    templates["tkinter"] = '''"""
Desktop GUI Chat - Generated with Open OTK

Modern dark-themed chat application featuring:
- Chat-bubble style messages with avatars
- Animated thinking indicator while generating
- Elapsed timer during generation
- Smooth hover effects on buttons
- Clear history, keyboard shortcuts, status bar
"""
import tkinter as tk
from tkinter import scrolledtext
import threading
import time as _time

from otk import ChatSession

COLORS = {
    "bg":           "#0d1117",
    "panel":        "#161b22",
    "card":         "#1c2128",
    "accent":       "#58a6ff",
    "accent_hover": "#79c0ff",
    "success":      "#3fb950",
    "error":        "#f85149",
    "text":         "#c9d1d9",
    "text_dim":     "#8b949e",
    "text_bright":  "#f0f6fc",
    "border":       "#30363d",
    "user_bg":      "#1a3a5c",
    "bot_bg":       "#1c2d1f",
}


class ChatGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Chat  -  __MODEL__")
        self.root.geometry("920x680")
        self.root.minsize(640, 480)
        self.root.configure(bg=COLORS["bg"])
        self._generating = False
        self._think_id = None

        self.session = ChatSession(
            "__MODEL__",
            system_message="You are a helpful assistant.",
            temperature=0.7,
        )
        self._build()

    # ── UI ────────────────────────────────────────────────────────

    def _build(self):
        # Header
        hdr = tk.Frame(self.root, bg=COLORS["panel"], height=60)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="AI Chat", font=("Segoe UI", 16, "bold"),
                 bg=COLORS["panel"], fg=COLORS["accent"]).pack(side=tk.LEFT, padx=24, pady=14)
        tk.Label(hdr, text="__MODEL__", font=("Segoe UI", 10),
                 bg=COLORS["panel"], fg=COLORS["text_dim"]).pack(side=tk.LEFT)

        clear_btn = tk.Label(hdr, text="  Clear Chat  ", font=("Segoe UI", 9),
                             bg=COLORS["card"], fg=COLORS["text_dim"], cursor="hand2")
        clear_btn.pack(side=tk.RIGHT, padx=20, pady=16)
        clear_btn.bind("<Button-1>", lambda _: self._clear())
        clear_btn.bind("<Enter>", lambda _: clear_btn.config(bg=COLORS["accent"], fg=COLORS["text_bright"]))
        clear_btn.bind("<Leave>", lambda _: clear_btn.config(bg=COLORS["card"], fg=COLORS["text_dim"]))

        # Chat area (canvas + scrollbar for custom bubbles)
        self.chat = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, bg=COLORS["bg"], fg=COLORS["text"],
            font=("Segoe UI", 10), borderwidth=0, highlightthickness=0,
            insertbackground=COLORS["bg"], padx=24, pady=16, cursor="arrow",
            selectbackground=COLORS["accent"], spacing3=4,
        )
        self.chat.pack(fill=tk.BOTH, expand=True)
        self.chat.config(state=tk.DISABLED)

        self.chat.tag_config("user_name", foreground=COLORS["accent"],
                             font=("Segoe UI", 9, "bold"), spacing1=14)
        self.chat.tag_config("bot_name", foreground=COLORS["success"],
                             font=("Segoe UI", 9, "bold"), spacing1=14)
        self.chat.tag_config("user_msg", foreground=COLORS["text"],
                             font=("Segoe UI", 10), lmargin1=12, lmargin2=12,
                             background=COLORS["user_bg"], spacing1=4, spacing3=4)
        self.chat.tag_config("bot_msg", foreground=COLORS["text"],
                             font=("Segoe UI", 10), lmargin1=12, lmargin2=12,
                             background=COLORS["bot_bg"], spacing1=4, spacing3=4)
        self.chat.tag_config("thinking", foreground=COLORS["text_dim"],
                             font=("Segoe UI", 10, "italic"), lmargin1=12)
        self.chat.tag_config("info", foreground=COLORS["text_dim"],
                             font=("Segoe UI", 9, "italic"), justify=tk.CENTER)
        self.chat.tag_config("spacer", font=("Segoe UI", 4))

        # Input bar
        bar = tk.Frame(self.root, bg=COLORS["panel"])
        bar.pack(fill=tk.X)
        inner = tk.Frame(bar, bg=COLORS["panel"])
        inner.pack(fill=tk.X, padx=20, pady=14)

        input_frame = tk.Frame(inner, bg=COLORS["card"], highlightthickness=1,
                               highlightbackground=COLORS["border"],
                               highlightcolor=COLORS["accent"])
        input_frame.pack(fill=tk.X)

        self.entry = tk.Entry(
            input_frame, font=("Segoe UI", 11), bg=COLORS["card"],
            fg=COLORS["text"], insertbackground=COLORS["accent"], borderwidth=0,
        )
        self.entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=16, pady=12, ipady=3)
        self.entry.bind("<Return>", lambda _: self._send())
        self.entry.focus()

        self.send_btn = tk.Button(
            input_frame, text="  Send  ", command=self._send,
            font=("Segoe UI", 10, "bold"), bg=COLORS["accent"],
            fg=COLORS["text_bright"], activebackground=COLORS["accent_hover"],
            activeforeground=COLORS["text_bright"], relief="flat", cursor="hand2",
            borderwidth=0, padx=16, pady=6,
        )
        self.send_btn.pack(side=tk.RIGHT, padx=8, pady=8)
        self.send_btn.bind("<Enter>", lambda _: self.send_btn.config(bg=COLORS["accent_hover"]))
        self.send_btn.bind("<Leave>", lambda _: self.send_btn.config(bg=COLORS["accent"]))

        # Status
        self.status = tk.Label(self.root, text="Ready", font=("Segoe UI", 9),
                               bg=COLORS["bg"], fg=COLORS["text_dim"], anchor=tk.W, padx=24)
        self.status.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 6))

    # ── Chat helpers ──────────────────────────────────────────────

    def _insert(self, text, tag=""):
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, text, tag)
        self.chat.see(tk.END)
        self.chat.config(state=tk.DISABLED)

    def _add_message(self, role, text):
        if role == "user":
            self._insert("You\\n", "user_name")
            self._insert(f" {text} \\n", "user_msg")
        else:
            self._insert("Assistant\\n", "bot_name")
            self._insert(f" {text} \\n", "bot_msg")
        self._insert("\\n", "spacer")

    # ── Thinking animation ────────────────────────────────────────

    def _start_thinking(self):
        self._generating = True
        self._think_start = _time.time()
        self._think_frame = 0
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, "Assistant\\n", "bot_name")
        self._think_mark = self.chat.index(tk.END)
        self.chat.insert(tk.END, " Thinking ...\\n", "thinking")
        self.chat.see(tk.END)
        self.chat.config(state=tk.DISABLED)
        self._animate_thinking()

    def _animate_thinking(self):
        if not self._generating:
            return
        dots = [".", "..", "...", ".. ", ".  ", "   "]
        elapsed = _time.time() - self._think_start
        t_str = f"{elapsed:.0f}s" if elapsed < 60 else f"{int(elapsed)//60}m {int(elapsed)%60:02d}s"
        text = f" Thinking {dots[self._think_frame % len(dots)]}  ({t_str})\\n"
        self.chat.config(state=tk.NORMAL)
        self.chat.delete(self._think_mark + " -1l linestart", self._think_mark)
        self.chat.insert(self._think_mark + " -1l linestart", text, "thinking")
        self.chat.see(tk.END)
        self.chat.config(state=tk.DISABLED)
        self._think_frame += 1
        self._think_id = self.root.after(400, self._animate_thinking)

    def _stop_thinking(self):
        self._generating = False
        if self._think_id:
            self.root.after_cancel(self._think_id)
            self._think_id = None
        self.chat.config(state=tk.NORMAL)
        try:
            self.chat.delete(self._think_mark + " -2l linestart", tk.END)
        except Exception:
            pass
        self.chat.config(state=tk.DISABLED)

    # ── Send / Clear ──────────────────────────────────────────────

    def _send(self):
        msg = self.entry.get().strip()
        if not msg or self._generating:
            return
        self.entry.delete(0, tk.END)
        self._add_message("user", msg)
        self.send_btn.config(state=tk.DISABLED, bg=COLORS["border"])
        self.entry.config(state=tk.DISABLED)
        self.status.config(text="Generating...", fg=COLORS["accent"])
        self._start_thinking()

        def worker():
            try:
                response = self.session.send(msg)
                self.root.after(0, self._stop_thinking)
                self.root.after(10, lambda: self._add_message("bot", response))
                self.root.after(10, lambda: self.status.config(text="Ready", fg=COLORS["text_dim"]))
            except Exception as e:
                self.root.after(0, self._stop_thinking)
                self.root.after(10, lambda: self._insert(f"Error: {e}\\n", "info"))
                self.root.after(10, lambda: self.status.config(text="Error", fg=COLORS["error"]))
            finally:
                self.root.after(0, lambda: self.send_btn.config(state=tk.NORMAL, bg=COLORS["accent"]))
                self.root.after(0, lambda: self.entry.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.entry.focus())

        threading.Thread(target=worker, daemon=True).start()

    def _clear(self):
        self.session.clear_history()
        self.chat.config(state=tk.NORMAL)
        self.chat.delete("1.0", tk.END)
        self.chat.config(state=tk.DISABLED)
        self._insert("Chat history cleared.\\n", "info")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    ChatGUI().run()
'''

    # ── 7. Advanced Tkinter GUI ───────────────────────────────────────
    templates["tkinter_advanced"] = '''"""
Advanced Desktop GUI - Generated with Open OTK

Sidebar-navigation chat application featuring:
- Sidebar with page switching (Chat / Generate), model & temp controls
- Editable system prompt with apply + visual feedback
- Chat bubbles with animated thinking indicator and elapsed timer
- Content generation page
- No ttk.Notebook - uses clean page switching like the OTK v2 main app
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time as _time

from otk import ChatSession, OllamaClient, ModelManager

C = {
    "bg":           "#0d1117",
    "panel":        "#161b22",
    "sidebar":      "#010409",
    "card":         "#1c2128",
    "hover":        "#21262d",
    "accent":       "#58a6ff",
    "accent_h":     "#79c0ff",
    "accent_dim":   "#1f6feb",
    "success":      "#3fb950",
    "error":        "#f85149",
    "warning":      "#d29922",
    "text":         "#c9d1d9",
    "text_dim":     "#8b949e",
    "text_bright":  "#f0f6fc",
    "border":       "#30363d",
    "user_bg":      "#1a3a5c",
    "bot_bg":       "#1c2d1f",
}


def _hover_btn(widget, normal_bg, normal_fg, hover_bg, hover_fg):
    widget.bind("<Enter>", lambda _: widget.config(bg=hover_bg, fg=hover_fg))
    widget.bind("<Leave>", lambda _: widget.config(bg=normal_bg, fg=normal_fg))


class AdvancedChatGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Advanced AI Chat  -  Open OTK")
        self.root.geometry("1120x760")
        self.root.minsize(900, 580)
        self.root.configure(bg=C["bg"])

        self.client = OllamaClient()
        self.manager = ModelManager()
        self.current_model = "__MODEL__"
        self.temperature = 0.7
        self.system_msg = "You are a helpful assistant."
        self.session = ChatSession(self.current_model, system_message=self.system_msg,
                                   temperature=self.temperature)
        self._generating = False
        self._think_id = None
        self._msg_count = 0
        self._current_page = None
        self._nav_labels = {}

        s = ttk.Style()
        s.theme_use("clam")
        s.configure("TCombobox", fieldbackground=C["card"], background=C["card"],
                    foreground=C["text"], arrowcolor=C["accent"])
        s.map("TCombobox", fieldbackground=[("readonly", C["card"])],
              selectbackground=[("readonly", C["accent"])])

        self._build()
        self.root.after(200, self._refresh_models)

    # ── Layout ────────────────────────────────────────────────────

    def _build(self):
        outer = tk.Frame(self.root, bg=C["bg"])
        outer.pack(fill=tk.BOTH, expand=True)

        sb = tk.Frame(outer, bg=C["sidebar"], width=230)
        sb.pack(side=tk.LEFT, fill=tk.Y)
        sb.pack_propagate(False)
        self._build_sidebar(sb)

        self._content = tk.Frame(outer, bg=C["bg"])
        self._content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._pages = {}
        self._build_chat_page()
        self._build_gen_page()
        self._navigate("chat")

        self.status = tk.Label(self._content, font=("Segoe UI", 9), bg=C["sidebar"],
                               fg=C["text_dim"], anchor=tk.W, padx=20, pady=6)
        self.status.pack(fill=tk.X, side=tk.BOTTOM)
        self._update_status()

    def _build_sidebar(self, p):
        tk.Label(p, text="OTK Chat", font=("Segoe UI", 18, "bold"),
                 bg=C["sidebar"], fg=C["accent"]).pack(padx=18, pady=(22, 0), anchor=tk.W)
        tk.Label(p, text="v2.0", font=("Segoe UI", 9),
                 bg=C["sidebar"], fg=C["text_dim"]).pack(padx=18, anchor=tk.W)

        tk.Frame(p, bg=C["border"], height=1).pack(fill=tk.X, padx=14, pady=(14, 10))

        # Navigation
        for key, label in [("chat", "Chat"), ("generate", "Generate")]:
            nav = tk.Label(p, text=f"  {label}", font=("Segoe UI", 10),
                           bg=C["sidebar"], fg=C["text_dim"], anchor=tk.W,
                           padx=18, pady=8, cursor="hand2")
            nav.pack(fill=tk.X)
            nav.bind("<Button-1>", lambda _, k=key: self._navigate(k))
            self._nav_labels[key] = nav

        tk.Frame(p, bg=C["border"], height=1).pack(fill=tk.X, padx=14, pady=(10, 10))

        # Model
        tk.Label(p, text="Model", font=("Segoe UI", 9, "bold"),
                 bg=C["sidebar"], fg=C["text"]).pack(padx=18, anchor=tk.W)
        self.model_var = tk.StringVar(value=self.current_model)
        self.model_combo = ttk.Combobox(p, textvariable=self.model_var,
                                        font=("Segoe UI", 9), state="readonly", width=22)
        self.model_combo.pack(padx=18, pady=(4, 10), anchor=tk.W)
        self.model_combo.bind("<<ComboboxSelected>>", lambda _: self._on_model_change())

        # Temperature
        tk.Label(p, text="Temperature", font=("Segoe UI", 9, "bold"),
                 bg=C["sidebar"], fg=C["text"]).pack(padx=18, anchor=tk.W)
        tr = tk.Frame(p, bg=C["sidebar"])
        tr.pack(padx=18, fill=tk.X, pady=(4, 10))
        self.temp_var = tk.DoubleVar(value=0.7)
        self.temp_lbl = tk.Label(tr, text="0.7", font=("Segoe UI", 9),
                                 bg=C["sidebar"], fg=C["accent"], width=4)
        self.temp_lbl.pack(side=tk.RIGHT)
        tk.Scale(tr, from_=0.0, to=2.0, resolution=0.1, orient=tk.HORIZONTAL,
                 variable=self.temp_var, bg=C["sidebar"], fg=C["text"],
                 highlightthickness=0, troughcolor=C["card"],
                 activebackground=C["accent"], length=130, sliderlength=16,
                 showvalue=False, command=lambda v: self._on_temp_change(v)).pack(side=tk.LEFT)

        tk.Frame(p, bg=C["border"], height=1).pack(fill=tk.X, padx=14, pady=(0, 10))

        # System prompt
        tk.Label(p, text="System Prompt", font=("Segoe UI", 9, "bold"),
                 bg=C["sidebar"], fg=C["text"]).pack(padx=18, anchor=tk.W)
        self.sys_text = tk.Text(p, font=("Segoe UI", 9), bg=C["card"],
                                fg=C["text"], insertbackground=C["accent"],
                                relief="flat", highlightthickness=1,
                                highlightbackground=C["border"],
                                highlightcolor=C["accent"], height=3, wrap=tk.WORD)
        self.sys_text.pack(padx=18, fill=tk.X, pady=(4, 6))
        self.sys_text.insert("1.0", self.system_msg)

        self.apply_btn = tk.Label(p, text="  Apply & Reset Chat  ", font=("Segoe UI", 9),
                                  bg=C["card"], fg=C["accent"], cursor="hand2", pady=4)
        self.apply_btn.pack(padx=18, anchor=tk.W, pady=(0, 8))
        self.apply_btn.bind("<Button-1>", lambda _: self._apply_system())
        _hover_btn(self.apply_btn, C["card"], C["accent"], C["accent"], C["text_bright"])

        # Session info
        tk.Frame(p, bg=C["border"], height=1).pack(fill=tk.X, padx=14, pady=(0, 10))
        self.msg_lbl = tk.Label(p, text="Messages: 0", font=("Segoe UI", 9),
                                bg=C["sidebar"], fg=C["text_dim"])
        self.msg_lbl.pack(padx=18, anchor=tk.W)

        # Spacer
        tk.Frame(p, bg=C["sidebar"]).pack(fill=tk.BOTH, expand=True)

        # New chat button at bottom
        new_btn = tk.Label(p, text="  New Chat  ", font=("Segoe UI", 10, "bold"),
                           bg=C["accent_dim"], fg=C["text_bright"], cursor="hand2",
                           pady=8)
        new_btn.pack(fill=tk.X, padx=14, pady=(4, 6))
        new_btn.bind("<Button-1>", lambda _: self._new_chat())
        _hover_btn(new_btn, C["accent_dim"], C["text_bright"], C["accent"], C["text_bright"])

        tk.Label(p, text="Open OTK", font=("Segoe UI", 8),
                 bg=C["sidebar"], fg=C["text_dim"]).pack(pady=(4, 12))

    # ── Pages ─────────────────────────────────────────────────────

    def _navigate(self, key):
        if self._current_page == key:
            return
        if self._current_page and self._current_page in self._pages:
            self._pages[self._current_page].pack_forget()
            nav = self._nav_labels.get(self._current_page)
            if nav:
                nav.config(bg=C["sidebar"], fg=C["text_dim"])
        self._current_page = key
        self._pages[key].pack(fill=tk.BOTH, expand=True)
        nav = self._nav_labels.get(key)
        if nav:
            nav.config(bg=C["accent_dim"], fg=C["text_bright"])

    def _build_chat_page(self):
        page = tk.Frame(self._content, bg=C["bg"])
        self._pages["chat"] = page

        self.chat = scrolledtext.ScrolledText(
            page, wrap=tk.WORD, bg=C["bg"], fg=C["text"],
            font=("Segoe UI", 10), borderwidth=0, highlightthickness=0,
            insertbackground=C["bg"], padx=24, pady=16, cursor="arrow",
            selectbackground=C["accent"], spacing3=4,
        )
        self.chat.pack(fill=tk.BOTH, expand=True)
        self.chat.config(state=tk.DISABLED)
        self.chat.tag_config("user_name", foreground=C["accent"],
                             font=("Segoe UI", 9, "bold"), spacing1=14)
        self.chat.tag_config("bot_name", foreground=C["success"],
                             font=("Segoe UI", 9, "bold"), spacing1=14)
        self.chat.tag_config("user_msg", foreground=C["text"],
                             font=("Segoe UI", 10), lmargin1=12, lmargin2=12,
                             background=C["user_bg"], spacing1=4, spacing3=4)
        self.chat.tag_config("bot_msg", foreground=C["text"],
                             font=("Segoe UI", 10), lmargin1=12, lmargin2=12,
                             background=C["bot_bg"], spacing1=4, spacing3=4)
        self.chat.tag_config("thinking", foreground=C["text_dim"],
                             font=("Segoe UI", 10, "italic"), lmargin1=12)
        self.chat.tag_config("info", foreground=C["text_dim"],
                             font=("Segoe UI", 9, "italic"), justify=tk.CENTER)
        self.chat.tag_config("spacer", font=("Segoe UI", 4))

        bar = tk.Frame(page, bg=C["panel"])
        bar.pack(fill=tk.X)
        ib = tk.Frame(bar, bg=C["card"], highlightthickness=1,
                      highlightbackground=C["border"], highlightcolor=C["accent"])
        ib.pack(fill=tk.X, padx=20, pady=12)

        self.chat_entry = tk.Entry(
            ib, font=("Segoe UI", 11), bg=C["card"],
            fg=C["text"], insertbackground=C["accent"], borderwidth=0,
        )
        self.chat_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=16, pady=12, ipady=3)
        self.chat_entry.bind("<Return>", lambda _: self._send_chat())
        self.chat_entry.focus()

        self.chat_btn = tk.Button(
            ib, text="  Send  ", command=self._send_chat,
            font=("Segoe UI", 10, "bold"), bg=C["accent"],
            fg=C["text_bright"], activebackground=C["accent_h"],
            relief="flat", cursor="hand2", borderwidth=0, padx=16, pady=6,
        )
        self.chat_btn.pack(side=tk.RIGHT, padx=8, pady=8)
        _hover_btn(self.chat_btn, C["accent"], C["text_bright"], C["accent_h"], C["text_bright"])

    def _build_gen_page(self):
        page = tk.Frame(self._content, bg=C["bg"])
        self._pages["generate"] = page

        tk.Label(page, text="Content Generation", font=("Segoe UI", 18, "bold"),
                 bg=C["bg"], fg=C["accent"]).pack(anchor=tk.W, padx=28, pady=(24, 4))
        tk.Label(page, text="Enter a prompt and generate content with the selected model",
                 font=("Segoe UI", 9), bg=C["bg"],
                 fg=C["text_dim"]).pack(anchor=tk.W, padx=28, pady=(0, 16))

        tk.Label(page, text="Prompt", font=("Segoe UI", 10, "bold"),
                 bg=C["bg"], fg=C["text"]).pack(anchor=tk.W, padx=28)
        self.gen_input = scrolledtext.ScrolledText(
            page, height=5, bg=C["card"], fg=C["text"],
            font=("Segoe UI", 10), borderwidth=0, highlightthickness=1,
            highlightbackground=C["border"], highlightcolor=C["accent"],
            insertbackground=C["accent"], padx=14, pady=10,
        )
        self.gen_input.pack(fill=tk.X, padx=28, pady=(4, 12))

        self.gen_btn = tk.Button(
            page, text="  Generate  ", command=self._generate,
            font=("Segoe UI", 10, "bold"), bg=C["accent"],
            fg=C["text_bright"], relief="flat", cursor="hand2",
            activebackground=C["accent_h"], borderwidth=0, padx=20, pady=8,
        )
        self.gen_btn.pack(anchor=tk.W, padx=28, pady=(0, 12))
        _hover_btn(self.gen_btn, C["accent"], C["text_bright"], C["accent_h"], C["text_bright"])

        tk.Label(page, text="Output", font=("Segoe UI", 10, "bold"),
                 bg=C["bg"], fg=C["text"]).pack(anchor=tk.W, padx=28)
        self.gen_output = scrolledtext.ScrolledText(
            page, bg=C["card"], fg=C["text"],
            font=("Segoe UI", 10), borderwidth=0, highlightthickness=1,
            highlightbackground=C["border"], highlightcolor=C["accent"],
            insertbackground=C["accent"], padx=14, pady=10,
        )
        self.gen_output.pack(fill=tk.BOTH, expand=True, padx=28, pady=(4, 24))

    # ── Config ────────────────────────────────────────────────────

    def _refresh_models(self):
        try:
            models = self.manager.list_models()
            names = [m["name"] for m in models]
            self.model_combo["values"] = names
            if self.current_model in names:
                self.model_combo.set(self.current_model)
            elif names:
                self.model_combo.current(0)
                self._on_model_change()
        except Exception:
            pass

    def _on_model_change(self):
        self.current_model = self.model_var.get()
        self.session = ChatSession(self.current_model, system_message=self.system_msg,
                                   temperature=self.temperature)
        self._update_status()

    def _on_temp_change(self, val):
        self.temperature = float(val)
        self.temp_lbl.config(text=f"{self.temperature:.1f}")
        self.session = ChatSession(self.current_model, system_message=self.system_msg,
                                   temperature=self.temperature)
        self._update_status()

    def _apply_system(self):
        self.system_msg = self.sys_text.get("1.0", tk.END).strip()
        self.session = ChatSession(self.current_model, system_message=self.system_msg,
                                   temperature=self.temperature)
        self.chat.config(state=tk.NORMAL)
        self.chat.delete("1.0", tk.END)
        self.chat.config(state=tk.DISABLED)
        self._msg_count = 0
        self.msg_lbl.config(text="Messages: 0")
        self._ins("System prompt updated. Chat reset.\\n", "info")
        self._update_status("System prompt applied")
        self._navigate("chat")

    def _update_status(self, text=None):
        if text:
            self.status.config(text=text, fg=C["success"])
            self.root.after(3000, lambda: self.status.config(
                text=f"Ready  |  {self.current_model}  |  temp {self.temperature:.1f}",
                fg=C["text_dim"]))
        else:
            self.status.config(text=f"Ready  |  {self.current_model}  |  temp {self.temperature:.1f}",
                               fg=C["text_dim"])

    # ── Chat ──────────────────────────────────────────────────────

    def _ins(self, text, tag=""):
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, text, tag)
        self.chat.see(tk.END)
        self.chat.config(state=tk.DISABLED)

    def _add_msg(self, role, text):
        if role == "user":
            self._ins("You\\n", "user_name")
            self._ins(f" {text} \\n", "user_msg")
        else:
            self._ins("Assistant\\n", "bot_name")
            self._ins(f" {text} \\n", "bot_msg")
        self._ins("\\n", "spacer")
        self._msg_count += 1
        self.msg_lbl.config(text=f"Messages: {self._msg_count}")

    def _start_thinking(self):
        self._generating = True
        self._think_start = _time.time()
        self._think_frame = 0
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, "Assistant\\n", "bot_name")
        self._think_mark = self.chat.index(tk.END)
        self.chat.insert(tk.END, " Thinking ...\\n", "thinking")
        self.chat.see(tk.END)
        self.chat.config(state=tk.DISABLED)
        self._tick()

    def _tick(self):
        if not self._generating:
            return
        dots = [".", "..", "...", ".. ", ".  ", "   "]
        elapsed = _time.time() - self._think_start
        t = f"{elapsed:.0f}s" if elapsed < 60 else f"{int(elapsed)//60}m {int(elapsed)%60:02d}s"
        txt = f" Thinking {dots[self._think_frame % len(dots)]}  ({t})\\n"
        self.chat.config(state=tk.NORMAL)
        self.chat.delete(self._think_mark + " -1l linestart", self._think_mark)
        self.chat.insert(self._think_mark + " -1l linestart", txt, "thinking")
        self.chat.see(tk.END)
        self.chat.config(state=tk.DISABLED)
        self._think_frame += 1
        self._think_id = self.root.after(400, self._tick)

    def _stop_thinking(self):
        self._generating = False
        if self._think_id:
            self.root.after_cancel(self._think_id)
        self.chat.config(state=tk.NORMAL)
        try:
            self.chat.delete(self._think_mark + " -2l linestart", tk.END)
        except Exception:
            pass
        self.chat.config(state=tk.DISABLED)

    def _send_chat(self):
        msg = self.chat_entry.get().strip()
        if not msg or self._generating:
            return
        self.chat_entry.delete(0, tk.END)
        self._add_msg("user", msg)
        self.chat_btn.config(state=tk.DISABLED, bg=C["border"])
        self.chat_entry.config(state=tk.DISABLED)
        self.status.config(text="Generating...", fg=C["accent"])
        self._start_thinking()

        def worker():
            try:
                resp = self.session.send(msg)
                self.root.after(0, self._stop_thinking)
                self.root.after(10, lambda: self._add_msg("bot", resp))
                self.root.after(10, self._update_status)
            except Exception as e:
                self.root.after(0, self._stop_thinking)
                self.root.after(10, lambda: self._ins(f"Error: {e}\\n", "info"))
                self.root.after(10, lambda: self.status.config(text=f"Error", fg=C["error"]))
            finally:
                self.root.after(0, lambda: self.chat_btn.config(state=tk.NORMAL, bg=C["accent"]))
                self.root.after(0, lambda: self.chat_entry.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.chat_entry.focus())

        threading.Thread(target=worker, daemon=True).start()

    def _new_chat(self):
        if self._generating:
            return
        self.session = ChatSession(self.current_model, system_message=self.system_msg,
                                   temperature=self.temperature)
        self.chat.config(state=tk.NORMAL)
        self.chat.delete("1.0", tk.END)
        self.chat.config(state=tk.DISABLED)
        self._msg_count = 0
        self.msg_lbl.config(text="Messages: 0")
        self._ins("New conversation started.\\n", "info")
        self._navigate("chat")
        self.chat_entry.focus()
        self._update_status("New chat")

    def _generate(self):
        prompt = self.gen_input.get("1.0", tk.END).strip()
        if not prompt:
            return
        self.gen_output.delete("1.0", tk.END)
        self.gen_output.insert("1.0", "Generating...")
        self.gen_btn.config(state=tk.DISABLED, bg=C["border"])
        self.status.config(text="Generating content...", fg=C["warning"])

        def worker():
            try:
                result = self.client.generate(self.current_model, prompt,
                                              temperature=self.temperature)
                self.root.after(0, lambda: self.gen_output.delete("1.0", tk.END))
                self.root.after(0, lambda: self.gen_output.insert("1.0", result))
                self.root.after(0, self._update_status)
            except Exception as e:
                self.root.after(0, lambda: self.gen_output.delete("1.0", tk.END))
                self.root.after(0, lambda: self.gen_output.insert("1.0", f"Error: {e}"))
            finally:
                self.root.after(0, lambda: self.gen_btn.config(state=tk.NORMAL, bg=C["accent"]))

        threading.Thread(target=worker, daemon=True).start()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    AdvancedChatGUI().run()
'''

    content = templates.get(template_type, templates["chat"]).replace(_PLACEHOLDER, model)
    if not filename.endswith(".py"):
        filename += ".py"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)


# ─── Main Application with Sidebar ───────────────────────────────────

class OTKGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Open OTK v2.0")
        self.root.geometry("1280x820")
        self.root.minsize(1000, 650)
        self.root.configure(bg=COLORS["bg"])
        self.root.resizable(True, True)
        try:
            self.root.state("zoomed")
        except Exception:
            pass

        try:
            if os.name == "nt":
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        self._setup_style()
        self._check_ollama()

        # Layout
        outer = tk.Frame(self.root, bg=COLORS["bg"])
        outer.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = tk.Frame(outer, bg=COLORS["sidebar"], width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Content area
        self.content = tk.Frame(outer, bg=COLORS["bg"])
        self.content.pack(side="left", fill="both", expand=True)

        self._build_sidebar()

        # Pages
        self.pages = {}
        self._current_page = None
        self.pages["dashboard"] = DashboardPage(self.content, self)
        self.pages["chat"]      = ChatPage(self.content, self)
        self.pages["browse"]    = BrowseModelsPage(self.content, self)
        self.pages["manage"]    = ManageModelsPage(self.content, self)
        self.pages["evaluate"]  = EvaluationPage(self.content, self)
        self.pages["templates"] = TemplatePage(self.content, self)

        self.navigate("dashboard")

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("Treeview", background=COLORS["bg_secondary"],
                         foreground=COLORS["text"], fieldbackground=COLORS["bg_secondary"],
                         borderwidth=0, font=FONT_SMALL, rowheight=32)
        style.configure("Treeview.Heading", background=COLORS["bg_tertiary"],
                         foreground=COLORS["accent"], font=("Segoe UI", 10, "bold"),
                         relief="flat")
        style.map("Treeview",
                   background=[("selected", COLORS["accent"])],
                   foreground=[("selected", COLORS["text_bright"])])
        style.configure("TCombobox", fieldbackground=COLORS["bg_secondary"],
                         background=COLORS["bg_secondary"], foreground=COLORS["text"],
                         arrowcolor=COLORS["accent"], relief="flat")
        style.map("TCombobox",
                   fieldbackground=[("readonly", COLORS["bg_secondary"])],
                   selectbackground=[("readonly", COLORS["accent"])])

    def _check_ollama(self):
        try:
            c = OllamaClient()
            if not c.is_running():
                messagebox.showwarning("Ollama Not Running",
                    "Ollama is not running!\nStart Ollama first: https://ollama.ai")
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def _build_sidebar(self):
        # Logo
        logo_frame = tk.Frame(self.sidebar, bg=COLORS["sidebar"])
        logo_frame.pack(fill="x", pady=(20, 24))
        tk.Label(logo_frame, text="OTK", font=("Segoe UI", 24, "bold"),
                 bg=COLORS["sidebar"], fg=COLORS["accent"]).pack()
        tk.Label(logo_frame, text="v2.0", font=FONT_TINY,
                 bg=COLORS["sidebar"], fg=COLORS["text_dim"]).pack()

        sep = tk.Frame(self.sidebar, bg=COLORS["border"], height=1)
        sep.pack(fill="x", padx=16, pady=(0, 12))

        self._nav_buttons = {}
        nav_items = [
            ("dashboard",  "Dashboard"),
            ("chat",       "Chat"),
            ("browse",     "Browse Models"),
            ("manage",     "Manage Models"),
            ("evaluate",   "Evaluation Lab"),
            ("templates",  "Templates"),
        ]
        for key, label in nav_items:
            btn = tk.Label(self.sidebar, text=f"  {label}", font=FONT_SMALL,
                           bg=COLORS["sidebar"], fg=COLORS["text_secondary"],
                           anchor="w", padx=20, pady=10, cursor="hand2")
            btn.pack(fill="x")
            btn.bind("<Button-1>", lambda _, k=key: self.navigate(k))
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=COLORS["sidebar_hover"])
                     if b != self._nav_buttons.get(self._current_page) else None)
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=COLORS["sidebar"])
                     if b != self._nav_buttons.get(self._current_page) else None)
            self._nav_buttons[key] = btn

        # Spacer
        tk.Frame(self.sidebar, bg=COLORS["sidebar"]).pack(fill="both", expand=True)

        # Footer
        sep2 = tk.Frame(self.sidebar, bg=COLORS["border"], height=1)
        sep2.pack(fill="x", padx=16, pady=(0, 8))

        gh = tk.Label(self.sidebar, text="  Documentations", font=FONT_TINY,
                      bg=COLORS["sidebar"], fg=COLORS["accent"], cursor="hand2",
                      anchor="w", padx=20, pady=6)
        gh.pack(fill="x")
        gh.bind("<Button-1>", lambda _: webbrowser.open("https://abidhasanrafi.github.io/otk/"))

        tk.Label(self.sidebar, text="  Md. Abid Hasan Rafi", font=FONT_TINY,
                 bg=COLORS["sidebar"], fg=COLORS["text_dim"],
                 anchor="w", padx=20).pack(fill="x", side="bottom", pady=(0, 14))

    def navigate(self, page_key):
        if self._current_page == page_key:
            return
        # Hide current
        if self._current_page and self._current_page in self.pages:
            self.pages[self._current_page].pack_forget()
            btn = self._nav_buttons.get(self._current_page)
            if btn:
                btn.config(bg=COLORS["sidebar"], fg=COLORS["text_secondary"])

        # Show new
        self._current_page = page_key
        self.pages[page_key].pack(fill="both", expand=True)
        btn = self._nav_buttons.get(page_key)
        if btn:
            btn.config(bg=COLORS["sidebar_active"], fg=COLORS["text_bright"])

    def run_command(self, command, title="Command"):
        """Run an Ollama command in a popup terminal."""
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("750x450")
        win.configure(bg=COLORS["bg"])

        tk.Label(win, text=title, font=FONT_HEADING, bg=COLORS["bg"],
                 fg=COLORS["accent"]).pack(pady=(12, 4))
        tk.Label(win, text=f"$ {command}", font=FONT_MONO, bg=COLORS["bg_secondary"],
                 fg=COLORS["text_secondary"], anchor="w", padx=12, pady=6).pack(fill="x", padx=12)

        output = scrolledtext.ScrolledText(win, font=FONT_MONO, bg=COLORS["bg_tertiary"],
                                           fg=COLORS["text"], relief="flat", wrap="word")
        output.pack(fill="both", expand=True, padx=12, pady=8)

        RoundedButton(win, text="Close", command=win.destroy, bg=COLORS["error"],
                      width=100, height=32).pack(pady=(0, 12))

        def _run():
            try:
                proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, text=True,
                                        encoding="utf-8", errors="replace", bufsize=1)
                for line in proc.stdout:
                    output.insert(tk.END, line)
                    output.see(tk.END)
                    output.update()
                proc.wait()
                msg = "\nDone!\n" if proc.returncode == 0 else f"\nFailed (code {proc.returncode})\n"
                output.insert(tk.END, msg)
                output.see(tk.END)
            except Exception as e:
                output.insert(tk.END, f"\nError: {e}\n")

        threading.Thread(target=_run, daemon=True).start()

    def run(self):
        self.root.mainloop()


def main():
    import argparse
    parser = argparse.ArgumentParser(prog="otk", description="Open OTK v2.0")
    parser.add_argument("--version", "-v", action="version",
                        version="Open OTK v2.0.0\nAuthor: Md. Abid Hasan Rafi\nLicense: MIT")
    parser.parse_args()

    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("Missing dependencies. Run: pip install requests beautifulsoup4")
        sys.exit(1)

    app = OTKGUI()
    app.run()


if __name__ == "__main__":
    main()
