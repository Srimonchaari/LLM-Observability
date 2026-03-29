from fastapi import FastAPI
from prometheus_client import make_asgi_app

from app.config import settings
from app.routes.chat import router as chat_router
from app.routes.health import router as health_router

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Lightweight observability starter for LLM cost and latency metrics.",
)

app.include_router(health_router)
app.include_router(chat_router)
app.mount("/metrics", make_asgi_app())


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": settings.app_name,
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
    }
