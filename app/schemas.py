from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    provider: str = Field(default="openai", examples=["openai"])
    model: str = Field(default="gpt-4o-mini", examples=["gpt-4o-mini"])
    feature: str = Field(default="chat", examples=["support-bot"])
    endpoint: str = Field(default="/chat", examples=["/chat"])
    prompt: str = Field(..., min_length=1, examples=["Summarize the incident"])
    max_output_tokens: int = Field(default=128, ge=1, le=4096)


class ChatResponse(BaseModel):
    provider: str
    model: str
    feature: str
    endpoint: str
    response: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    latency_ms: float
    status: str


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
