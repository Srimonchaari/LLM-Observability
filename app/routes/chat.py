import time

from fastapi import APIRouter, HTTPException

from app.metrics import record_request
from app.schemas import ChatRequest, ChatResponse
from app.simulator import FakeLLMSimulator, LLMProviderError

router = APIRouter(tags=["chat"])
simulator = FakeLLMSimulator()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    start_time = time.perf_counter()

    try:
        result = simulator.generate(
            provider=request.provider,
            model=request.model,
            prompt=request.prompt,
            max_output_tokens=request.max_output_tokens,
        )
        status = "success"

        record_request(
            provider=request.provider,
            model=request.model,
            endpoint=request.endpoint,
            feature=request.feature,
            status=status,
            latency_seconds=result.latency_seconds,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            estimated_cost_usd=result.estimated_cost_usd,
        )

        return ChatResponse(
            provider=request.provider,
            model=request.model,
            feature=request.feature,
            endpoint=request.endpoint,
            response=result.text,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            estimated_cost_usd=result.estimated_cost_usd,
            latency_ms=round(result.latency_seconds * 1000, 2),
            status=status,
        )

    except LLMProviderError as exc:
        elapsed_seconds = time.perf_counter() - start_time
        status = "error"

        # Even failed requests usually incur some work. Record a small amount.
        record_request(
            provider=request.provider,
            model=request.model,
            endpoint=request.endpoint,
            feature=request.feature,
            status=status,
            latency_seconds=elapsed_seconds,
            input_tokens=max(1, len(request.prompt.split()) * 2),
            output_tokens=0,
            estimated_cost_usd=0.0,
        )

        raise HTTPException(status_code=502, detail=str(exc)) from exc
