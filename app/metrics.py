from prometheus_client import Counter, Histogram


LABEL_NAMES = ["provider", "model", "endpoint", "feature", "status"]


REQUESTS_TOTAL = Counter(
    "llm_requests_total",
    "Total number of LLM requests.",
    LABEL_NAMES,
)

ERRORS_TOTAL = Counter(
    "llm_errors_total",
    "Total number of failed LLM requests.",
    LABEL_NAMES,
)

INPUT_TOKENS_TOTAL = Counter(
    "llm_input_tokens_total",
    "Total number of input tokens processed.",
    LABEL_NAMES,
)

OUTPUT_TOKENS_TOTAL = Counter(
    "llm_output_tokens_total",
    "Total number of output tokens generated.",
    LABEL_NAMES,
)

ESTIMATED_COST_USD_TOTAL = Counter(
    "llm_estimated_cost_usd_total",
    "Estimated LLM cost in USD.",
    LABEL_NAMES,
)

REQUEST_LATENCY_SECONDS = Histogram(
    "llm_request_latency_seconds",
    "Latency of LLM requests in seconds.",
    LABEL_NAMES,
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 3, 5, 8, 13, 21),
)


def record_request(
    *,
    provider: str,
    model: str,
    endpoint: str,
    feature: str,
    status: str,
    latency_seconds: float,
    input_tokens: int,
    output_tokens: int,
    estimated_cost_usd: float,
) -> None:
    """Record the full metric set for a request."""

    labels = {
        "provider": provider,
        "model": model,
        "endpoint": endpoint,
        "feature": feature,
        "status": status,
    }

    REQUESTS_TOTAL.labels(**labels).inc()
    INPUT_TOKENS_TOTAL.labels(**labels).inc(input_tokens)
    OUTPUT_TOKENS_TOTAL.labels(**labels).inc(output_tokens)
    ESTIMATED_COST_USD_TOTAL.labels(**labels).inc(estimated_cost_usd)
    REQUEST_LATENCY_SECONDS.labels(**labels).observe(latency_seconds)

    if status != "success":
        ERRORS_TOTAL.labels(**labels).inc()
