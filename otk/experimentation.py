"""
Experimentation and Testing Toolkit

Tools for experimenting with models, comparing outputs,
running tests, and exploring capabilities.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class ExperimentResult:
    """Result from a single experiment"""
    model: str
    prompt: str
    response: str
    time_taken: float
    tokens_estimated: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class ComparisonResult:
    """Results from comparing multiple models"""
    models: List[str]
    prompt: str
    results: List[ExperimentResult]
    winner: Optional[str] = None
    rankings: Dict[str, float] = field(default_factory=dict)


class ModelExperiment:
    """
    Run experiments with one or more models
    
    Example:
        >>> exp = ModelExperiment()
        >>> results = exp.compare_models(
        ...     models=["llama2", "mistral"],
        ...     prompt="What is Python?"
        ... )
        >>> exp.print_comparison(results)
    """
    
    def __init__(self, client: Optional[Any] = None):
        """Initialize experiment runner"""
        from .client import OllamaClient
        self.client = client or OllamaClient()
    
    def run_single(
        self,
        model: str,
        prompt: str,
        **kwargs
    ) -> ExperimentResult:
        """
        Run single model test
        
        Args:
            model: Model name
            prompt: Prompt to test
            **kwargs: Additional parameters
            
        Returns:
            ExperimentResult
        """
        start_time = time.time()
        
        try:
            response = self.client.generate(model, prompt, **kwargs)
            time_taken = time.time() - start_time
            
            # Estimate tokens
            from .utils import estimate_tokens
            tokens = estimate_tokens(response)
            
            return ExperimentResult(
                model=model,
                prompt=prompt,
                response=response,
                time_taken=time_taken,
                tokens_estimated=tokens,
                metadata={'success': True}
            )
            
        except Exception as e:
            return ExperimentResult(
                model=model,
                prompt=prompt,
                response="",
                time_taken=time.time() - start_time,
                tokens_estimated=0,
                error=str(e),
                metadata={'success': False}
            )
    
    def compare_models(
        self,
        models: List[str],
        prompt: str,
        parallel: bool = False,
        **kwargs
    ) -> ComparisonResult:
        """
        Compare multiple models on same prompt
        
        Args:
            models: List of model names
            prompt: Prompt to test
            parallel: Run in parallel
            **kwargs: Additional parameters
            
        Returns:
            ComparisonResult
        """
        results = []
        
        if parallel:
            with ThreadPoolExecutor(max_workers=len(models)) as executor:
                future_to_model = {
                    executor.submit(self.run_single, model, prompt, **kwargs): model
                    for model in models
                }
                
                for future in as_completed(future_to_model):
                    results.append(future.result())
        else:
            for model in models:
                results.append(self.run_single(model, prompt, **kwargs))
        
        # Calculate rankings (by speed)
        rankings = {
            r.model: r.time_taken
            for r in results if not r.error
        }
        
        # Find fastest
        winner = min(rankings, key=rankings.get) if rankings else None
        
        return ComparisonResult(
            models=models,
            prompt=prompt,
            results=results,
            winner=winner,
            rankings=rankings
        )
    
    def batch_test(
        self,
        model: str,
        prompts: List[str],
        **kwargs
    ) -> List[ExperimentResult]:
        """
        Test model with multiple prompts
        
        Args:
            model: Model name
            prompts: List of prompts
            **kwargs: Additional parameters
            
        Returns:
            List of ExperimentResults
        """
        return [
            self.run_single(model, prompt, **kwargs)
            for prompt in prompts
        ]
    
    def benchmark(
        self,
        model: str,
        prompt: str,
        iterations: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Benchmark model performance
        
        Args:
            model: Model name
            prompt: Test prompt
            iterations: Number of iterations
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with benchmark stats
        """
        results = []
        
        for _ in range(iterations):
            result = self.run_single(model, prompt, **kwargs)
            if not result.error:
                results.append(result)
        
        if not results:
            return {'error': 'All iterations failed'}
        
        times = [r.time_taken for r in results]
        tokens = [r.tokens_estimated for r in results]
        
        return {
            'model': model,
            'iterations': len(results),
            'avg_time': statistics.mean(times),
            'min_time': min(times),
            'max_time': max(times),
            'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
            'avg_tokens': statistics.mean(tokens),
            'tokens_per_second': statistics.mean([t / time for t, time in zip(tokens, times)]),
        }
    
    def print_comparison(self, result: ComparisonResult):
        """Pretty print comparison results"""
        print("\n" + "=" * 70)
        print(f"Model Comparison: {result.prompt[:50]}...")
        print("=" * 70)
        
        for exp in result.results:
            print(f"\n🤖 {exp.model}")
            print(f"{'─' * 70}")
            
            if exp.error:
                print(f"❌ Error: {exp.error}")
            else:
                print(f"Response: {exp.response[:200]}...")
                print(f"\n⏱️  Time: {exp.time_taken:.2f}s")
                print(f"📝 Tokens: ~{exp.tokens_estimated}")
                print(f"🚀 Speed: ~{exp.tokens_estimated / exp.time_taken:.1f} tokens/s")
        
        if result.winner:
            print(f"\n🏆 Fastest: {result.winner} ({result.rankings[result.winner]:.2f}s)")
    
    def print_benchmark(self, stats: Dict[str, Any]):
        """Pretty print benchmark results"""
        print("\n" + "=" * 70)
        print(f"Benchmark Results: {stats.get('model', 'Unknown')}")
        print("=" * 70)
        
        if 'error' in stats:
            print(f"❌ {stats['error']}")
            return
        
        print(f"\n📊 Iterations: {stats['iterations']}")
        print(f"⏱️  Average Time: {stats['avg_time']:.2f}s")
        print(f"⚡ Min Time: {stats['min_time']:.2f}s")
        print(f"🐌 Max Time: {stats['max_time']:.2f}s")
        print(f"📈 Std Dev: {stats['std_dev']:.2f}s")
        print(f"📝 Avg Tokens: {stats['avg_tokens']:.0f}")
        print(f"🚀 Tokens/Second: {stats['tokens_per_second']:.1f}")


class ModelPlayground:
    """
    Interactive playground for experimenting with models
    
    Example:
        >>> playground = ModelPlayground()
        >>> playground.try_temperatures("llama2", "Write a story")
        >>> playground.try_prompt_variations("llama2", ["What is", "Explain"])
    """
    
    def __init__(self, client: Optional[Any] = None):
        """Initialize playground"""
        from .client import OllamaClient
        self.client = client or OllamaClient()
        self.experiment = ModelExperiment(client)
    
    def try_temperatures(
        self,
        model: str,
        prompt: str,
        temperatures: List[float] = None
    ):
        """
        Try different temperatures and see results
        
        Args:
            model: Model name
            prompt: Test prompt
            temperatures: List of temperatures to try
        """
        if temperatures is None:
            temperatures = [0.1, 0.5, 0.7, 0.9, 1.2]
        
        print(f"\n🌡️  Temperature Experiment: {model}")
        print(f"📝 Prompt: {prompt}")
        print("=" * 70)
        
        for temp in temperatures:
            print(f"\n🌡️  Temperature: {temp}")
            print("─" * 70)
            
            try:
                response = self.client.generate(model, prompt, temperature=temp)
                print(response[:300])
                if len(response) > 300:
                    print("...")
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def try_prompt_variations(
        self,
        model: str,
        base_prompt: str,
        variations: List[str]
    ):
        """
        Try different prompt formulations
        
        Args:
            model: Model name
            base_prompt: Base prompt
            variations: List of variations to append
        """
        print(f"\n📝 Prompt Variations Experiment: {model}")
        print("=" * 70)
        
        for i, variation in enumerate(variations, 1):
            full_prompt = f"{variation} {base_prompt}"
            print(f"\n{i}. {full_prompt}")
            print("─" * 70)
            
            try:
                response = self.client.generate(model, full_prompt)
                print(response[:200])
                if len(response) > 200:
                    print("...")
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def try_system_messages(
        self,
        model: str,
        prompt: str,
        system_messages: List[str]
    ):
        """
        Try different system messages
        
        Args:
            model: Model name
            prompt: Test prompt
            system_messages: List of system messages to try
        """
        print(f"\n🎭 System Message Experiment: {model}")
        print(f"📝 Prompt: {prompt}")
        print("=" * 70)
        
        for i, system in enumerate(system_messages, 1):
            print(f"\n{i}. System: {system}")
            print("─" * 70)
            
            try:
                response = self.client.generate(model, prompt, system=system)
                print(response[:250])
                if len(response) > 250:
                    print("...")
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def find_best_temperature(
        self,
        model: str,
        prompt: str,
        eval_func: Callable[[str], float],
        temperature_range: tuple = (0.1, 1.5),
        steps: int = 10
    ) -> float:
        """
        Find optimal temperature using evaluation function
        
        Args:
            model: Model name
            prompt: Test prompt
            eval_func: Function that scores response (higher = better)
            temperature_range: Min/max temperature
            steps: Number of steps to try
            
        Returns:
            Best temperature found
        """
        min_temp, max_temp = temperature_range
        step_size = (max_temp - min_temp) / steps
        
        best_temp = min_temp
        best_score = -float('inf')
        
        print(f"\n🔍 Finding Best Temperature for: {model}")
        print("=" * 70)
        
        for i in range(steps + 1):
            temp = min_temp + (i * step_size)
            
            try:
                response = self.client.generate(model, prompt, temperature=temp)
                score = eval_func(response)
                
                print(f"Temp {temp:.2f}: Score {score:.2f}")
                
                if score > best_score:
                    best_score = score
                    best_temp = temp
                    
            except Exception as e:
                print(f"Temp {temp:.2f}: Error - {e}")
        
        print(f"\n🏆 Best Temperature: {best_temp:.2f} (Score: {best_score:.2f})")
        return best_temp


class ABTest:
    """
    A/B testing for model outputs
    
    Example:
        >>> ab = ABTest()
        >>> ab.test(
        ...     model_a="llama2",
        ...     model_b="mistral",
        ...     prompts=["Question 1", "Question 2"]
        ... )
    """
    
    def __init__(self, client: Optional[Any] = None):
        """Initialize A/B tester"""
        from .client import OllamaClient
        self.client = client or OllamaClient()
    
    def test(
        self,
        model_a: str,
        model_b: str,
        prompts: List[str],
        judge_func: Optional[Callable[[str, str], str]] = None
    ) -> Dict[str, Any]:
        """
        Run A/B test
        
        Args:
            model_a: First model
            model_b: Second model
            prompts: List of test prompts
            judge_func: Optional function to judge which is better
            
        Returns:
            Dictionary with results
        """
        results = {
            'model_a': model_a,
            'model_b': model_b,
            'wins_a': 0,
            'wins_b': 0,
            'ties': 0,
            'details': []
        }
        
        print(f"\n⚖️  A/B Test: {model_a} vs {model_b}")
        print("=" * 70)
        
        for i, prompt in enumerate(prompts, 1):
            print(f"\n📝 Test {i}/{len(prompts)}: {prompt[:50]}...")
            
            try:
                resp_a = self.client.generate(model_a, prompt)
                resp_b = self.client.generate(model_b, prompt)
                
                # Judge if function provided
                winner = None
                if judge_func:
                    winner = judge_func(resp_a, resp_b)
                
                # Update counts
                if winner == 'a':
                    results['wins_a'] += 1
                    print(f"🏆 Winner: {model_a}")
                elif winner == 'b':
                    results['wins_b'] += 1
                    print(f"🏆 Winner: {model_b}")
                else:
                    results['ties'] += 1
                    print("🤝 Tie")
                
                results['details'].append({
                    'prompt': prompt,
                    'response_a': resp_a,
                    'response_b': resp_b,
                    'winner': winner
                })
                
            except Exception as e:
                print(f"❌ Error: {e}")
        
        # Print summary
        print(f"\n{'=' * 70}")
        print("📊 A/B Test Results")
        print("=" * 70)
        print(f"{model_a}: {results['wins_a']} wins")
        print(f"{model_b}: {results['wins_b']} wins")
        print(f"Ties: {results['ties']}")
        
        return results
