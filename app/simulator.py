import random
import time
from dataclasses import dataclass


class LLMProviderError(Exception):
    """Raised when the fake LLM provider simulates a failure."""


@dataclass
class SimulationResult:
    text: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    latency_seconds: float


MODEL_PRICING_PER_1K_TOKENS = {
    ("openai", "gpt-4o-mini"): {"input": 0.00015, "output": 0.00060},
    ("openai", "gpt-4.1-mini"): {"input": 0.00040, "output": 0.00160},
    ("anthropic", "claude-3-5-haiku"): {"input": 0.00025, "output": 0.00125},
    ("google", "gemini-1.5-flash"): {"input": 0.00020, "output": 0.00080},
}

DEFAULT_PRICING = {"input": 0.00030, "output": 0.00120}
FAILURE_RATE = 0.08


class FakeLLMSimulator:
    """Fake LLM client for demo traffic and metrics collection."""

    def generate(
        self,
        *,
        provider: str,
        model: str,
        prompt: str,
        max_output_tokens: int,
    ) -> SimulationResult:
        pricing = MODEL_PRICING_PER_1K_TOKENS.get((provider, model), DEFAULT_PRICING)

        # Rough token estimate for demo purposes only.
        prompt_word_count = max(1, len(prompt.split()))
        input_tokens = prompt_word_count * random.randint(3, 6)

        output_tokens = random.randint(
            max(8, max_output_tokens // 4),
            max_output_tokens,
        )

        # Make latency feel more realistic by linking it to output size.
        base_latency = random.uniform(0.15, 0.6)
        output_latency = output_tokens * random.uniform(0.006, 0.012)
        jitter = random.uniform(0.0, 0.25)
        latency_seconds = round(base_latency + output_latency + jitter, 3)

        time.sleep(latency_seconds)

        # Error injection for demo dashboards.
        if random.random() < FAILURE_RATE:
            raise LLMProviderError(f"Simulated provider failure for {provider}/{model}")

        estimated_cost_usd = round(
            ((input_tokens / 1000) * pricing["input"])
            + ((output_tokens / 1000) * pricing["output"]),
            8,
        )

        response_text = (
            f"Fake response from {provider}/{model}. "
            f"Processed {input_tokens} input tokens and generated {output_tokens} output tokens."
        )

        return SimulationResult(
            text=response_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=estimated_cost_usd,
            latency_seconds=latency_seconds,
        )