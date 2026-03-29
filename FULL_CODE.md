# Full code for LLM Cost + Latency Monitor

## `.env.example`

```
APP_NAME=LLM Cost + Latency Monitor
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
DEFAULT_PROVIDER=openai
DEFAULT_MODEL=gpt-4o-mini
DEFAULT_FEATURE=chat

```

## `requirements.txt`

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
prometheus-client==0.20.0
pydantic==2.9.2
pydantic-settings==2.5.2
python-dotenv==1.0.1

```

## `Dockerfile`

```
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY .env.example ./.env.example

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

```

## `docker-compose.yml`

```yaml
version: "3.9"

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: llm-monitor-app
    ports:
      - "8000:8000"
    env_file:
      - .env.example
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:v2.54.1
    container_name: llm-monitor-prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports:
      - "9090:9090"
    depends_on:
      - app
    restart: unless-stopped

  grafana:
    image: grafana/grafana:11.2.0
    container_name: llm-monitor-grafana
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: admin
      GF_USERS_ALLOW_SIGN_UP: "false"
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - ./grafana/dashboards:/var/lib/grafana/dashboards:ro
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
    restart: unless-stopped

```

## `README.md`

```
# LLM Cost + Latency Monitor

A lightweight observability starter project for LLM applications.

It exposes Prometheus metrics from a FastAPI app and ships with a local Prometheus + Grafana stack for quick demos.

## What it tracks

- total requests
- total errors
- input tokens
- output tokens
- estimated USD cost
- request latency histogram

## Labels

All core metrics include these labels:

- `provider`
- `model`
- `endpoint`
- `feature`
- `status`

## Project structure

```text
llm-cost-latency-monitor/
├── app/
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   └── health.py
│   ├── __init__.py
│   ├── config.py
│   ├── main.py
│   ├── metrics.py
│   ├── schemas.py
│   └── simulator.py
├── grafana/
│   ├── dashboards/
│   │   └── llm-observability.json
│   └── provisioning/
│       ├── dashboards/
│       │   └── dashboard.yml
│       └── datasources/
│           └── datasource.yml
├── prometheus/
│   └── prometheus.yml
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Quick start

### Option 1: Run the full stack with Docker Compose

```bash
docker compose up --build
```

Services:

- FastAPI app: `http://localhost:8000`
- Metrics: `http://localhost:8000/metrics`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`
  - username: `admin`
  - password: `admin`

### Option 2: Run the app locally without Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Demo flow

1. Start the stack.
2. Send requests to `/chat`.
3. Open Grafana.
4. Use the preloaded dashboard named `LLM Cost + Latency Monitor`.

Example request:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "model": "gpt-4o-mini",
    "feature": "support-bot",
    "endpoint": "/chat",
    "prompt": "Summarize today\"s customer issues",
    "max_output_tokens": 120
  }'
```

Health check:

```bash
curl http://localhost:8000/health
```

## Sample PromQL queries

### Total requests

```promql
sum(llm_requests_total)
```

### Error rate

```promql
sum(rate(llm_errors_total[5m])) / sum(rate(llm_requests_total[5m]))
```

### p95 latency

```promql
histogram_quantile(0.95, sum(rate(llm_request_latency_seconds_bucket[5m])) by (le))
```

### Cost over time

```promql
sum(rate(llm_estimated_cost_usd_total[5m]))
```

### Tokens over time

```promql
sum(rate(llm_input_tokens_total[5m])) + sum(rate(llm_output_tokens_total[5m]))
```

### Cost by model

```promql
sum by (model) (rate(llm_estimated_cost_usd_total[5m]))
```

### Latency by endpoint

```promql
histogram_quantile(0.95, sum(rate(llm_request_latency_seconds_bucket[5m])) by (le, endpoint))
```

### Errors by model

```promql
sum by (model) (rate(llm_errors_total[5m]))
```

## How it works

1. A request hits the FastAPI `/chat` endpoint.
2. The app runs a fake LLM simulator instead of calling a real provider.
3. The simulator generates fake latency, fake token usage, a fake response, and occasional failures.
4. The app records Prometheus metrics with consistent labels.
5. Prometheus scrapes `/metrics` on a schedule.
6. Grafana reads Prometheus and shows the prebuilt dashboard.

## Notes

- This project is intentionally simple and demo-friendly.
- Estimated cost is computed from hardcoded per-1K token pricing in the simulator.
- No request data is stored outside Prometheus time series.

## Suggested v2 improvements

- Add middleware so every API endpoint is tracked automatically
- Add real provider integrations for OpenAI, Anthropic, Gemini, and open-source gateways
- Add request IDs and structured logs
- Add tracing with OpenTelemetry
- Split metrics into business metrics and infrastructure metrics
- Add per-tenant or per-project labels
- Add alert rules for cost spikes and latency regressions
- Add burn-rate style SLO alerts
- Add budget thresholds and daily cost rollups
- Add retry metrics and timeout metrics
- Add load testing scripts and synthetic traffic generator
- Add unit tests and integration tests

```

## `prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 5s
  evaluation_interval: 5s

scrape_configs:
  - job_name: "llm-monitor-app"
    metrics_path: /metrics
    static_configs:
      - targets: ["app:8000"]

```

## `grafana/provisioning/datasources/datasource.yml`

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false

```

## `grafana/provisioning/dashboards/dashboard.yml`

```yaml
apiVersion: 1

providers:
  - name: "LLM Dashboards"
    orgId: 1
    folder: ""
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /var/lib/grafana/dashboards

```

## `grafana/dashboards/llm-observability.json`

```json
{
  "annotations": {
    "list": [
      {
        "builtIn": 1,
        "datasource": {
          "type": "grafana",
          "uid": "-- Grafana --"
        },
        "enable": true,
        "hide": true,
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Annotations & Alerts",
        "type": "dashboard"
      }
    ]
  },
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 0,
  "id": null,
  "links": [],
  "liveNow": false,
  "panels": [
    {
      "datasource": {
        "type": "prometheus",
        "uid": "${DS_PROMETHEUS}"
      },
      "fieldConfig": {
        "defaults": {
          "unit": "short"
        },
        "overrides": []
      },
      "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
      "id": 1,
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {
          "calcs": ["lastNotNull"],
          "fields": "",
          "values": false
        },
        "textMode": "auto"
      },
      "targets": [
        {
          "expr": "sum(llm_requests_total)",
          "refId": "A"
        }
      ],
      "title": "Total Requests",
      "type": "stat"
    },
    {
      "datasource": {"type": "prometheus", "uid": "${DS_PROMETHEUS}"},
      "fieldConfig": {
        "defaults": {"unit": "percentunit", "decimals": 2},
        "overrides": []
      },
      "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0},
      "id": 2,
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": false},
        "textMode": "auto"
      },
      "targets": [
        {
          "expr": "sum(rate(llm_errors_total[5m])) / clamp_min(sum(rate(llm_requests_total[5m])), 1)",
          "refId": "A"
        }
      ],
      "title": "Error Rate",
      "type": "stat"
    },
    {
      "datasource": {"type": "prometheus", "uid": "${DS_PROMETHEUS}"},
      "fieldConfig": {
        "defaults": {"unit": "s", "decimals": 3},
        "overrides": []
      },
      "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0},
      "id": 3,
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": false},
        "textMode": "auto"
      },
      "targets": [
        {
          "expr": "histogram_quantile(0.95, sum(rate(llm_request_latency_seconds_bucket[5m])) by (le))",
          "refId": "A"
        }
      ],
      "title": "p95 Latency",
      "type": "stat"
    },
    {
      "datasource": {"type": "prometheus", "uid": "${DS_PROMETHEUS}"},
      "fieldConfig": {
        "defaults": {"unit": "currencyUSD"},
        "overrides": []
      },
      "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0},
      "id": 4,
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": false},
        "textMode": "auto"
      },
      "targets": [
        {
          "expr": "sum(increase(llm_estimated_cost_usd_total[1h]))",
          "refId": "A"
        }
      ],
      "title": "Cost, Last 1h",
      "type": "stat"
    },
    {
      "datasource": {"type": "prometheus", "uid": "${DS_PROMETHEUS}"},
      "fieldConfig": {"defaults": {"unit": "currencyUSD"}, "overrides": []},
      "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
      "id": 5,
      "options": {"legend": {"displayMode": "table", "placement": "bottom"}, "tooltip": {"mode": "multi", "sort": "none"}},
      "targets": [
        {
          "expr": "sum(rate(llm_estimated_cost_usd_total[5m]))",
          "legendFormat": "usd/sec",
          "refId": "A"
        }
      ],
      "title": "Cost Over Time",
      "type": "timeseries"
    },
    {
      "datasource": {"type": "prometheus", "uid": "${DS_PROMETHEUS}"},
      "fieldConfig": {"defaults": {"unit": "short"}, "overrides": []},
      "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
      "id": 6,
      "options": {"legend": {"displayMode": "table", "placement": "bottom"}, "tooltip": {"mode": "multi", "sort": "none"}},
      "targets": [
        {
          "expr": "sum(rate(llm_input_tokens_total[5m]))",
          "legendFormat": "input tokens/sec",
          "refId": "A"
        },
        {
          "expr": "sum(rate(llm_output_tokens_total[5m]))",
          "legendFormat": "output tokens/sec",
          "refId": "B"
        }
      ],
      "title": "Tokens Over Time",
      "type": "timeseries"
    },
    {
      "datasource": {"type": "prometheus", "uid": "${DS_PROMETHEUS}"},
      "fieldConfig": {"defaults": {"unit": "currencyUSD"}, "overrides": []},
      "gridPos": {"h": 8, "w": 8, "x": 0, "y": 16},
      "id": 7,
      "options": {"legend": {"displayMode": "list", "placement": "bottom"}, "tooltip": {"mode": "single", "sort": "none"}},
      "targets": [
        {
          "expr": "sum by (model) (rate(llm_estimated_cost_usd_total[5m]))",
          "legendFormat": "{{model}}",
          "refId": "A"
        }
      ],
      "title": "Cost by Model",
      "type": "barchart"
    },
    {
      "datasource": {"type": "prometheus", "uid": "${DS_PROMETHEUS}"},
      "fieldConfig": {"defaults": {"unit": "s"}, "overrides": []},
      "gridPos": {"h": 8, "w": 8, "x": 8, "y": 16},
      "id": 8,
      "options": {"legend": {"displayMode": "list", "placement": "bottom"}, "tooltip": {"mode": "multi", "sort": "none"}},
      "targets": [
        {
          "expr": "histogram_quantile(0.95, sum(rate(llm_request_latency_seconds_bucket[5m])) by (le, endpoint))",
          "legendFormat": "{{endpoint}}",
          "refId": "A"
        }
      ],
      "title": "Latency by Endpoint",
      "type": "timeseries"
    },
    {
      "datasource": {"type": "prometheus", "uid": "${DS_PROMETHEUS}"},
      "fieldConfig": {"defaults": {"unit": "short"}, "overrides": []},
      "gridPos": {"h": 8, "w": 8, "x": 16, "y": 16},
      "id": 9,
      "options": {"legend": {"displayMode": "list", "placement": "bottom"}, "tooltip": {"mode": "single", "sort": "none"}},
      "targets": [
        {
          "expr": "sum by (model) (rate(llm_errors_total[5m]))",
          "legendFormat": "{{model}}",
          "refId": "A"
        }
      ],
      "title": "Errors by Model",
      "type": "barchart"
    }
  ],
  "refresh": "5s",
  "schemaVersion": 39,
  "style": "dark",
  "tags": ["llm", "observability", "prometheus", "grafana"],
  "templating": {
    "list": [
      {
        "current": {"selected": false, "text": "Prometheus", "value": "Prometheus"},
        "hide": 0,
        "includeAll": false,
        "label": "datasource",
        "multi": false,
        "name": "DS_PROMETHEUS",
        "options": [],
        "query": "prometheus",
        "refresh": 1,
        "regex": "",
        "skipUrlSync": false,
        "type": "datasource"
      }
    ]
  },
  "time": {
    "from": "now-1h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "browser",
  "title": "LLM Cost + Latency Monitor",
  "uid": "llm-cost-latency-monitor",
  "version": 1,
  "weekStart": ""
}

```

## `app/config.py`

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "LLM Cost + Latency Monitor"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    default_provider: str = "openai"
    default_model: str = "gpt-4o-mini"
    default_feature: str = "chat"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()

```

## `app/schemas.py`

```python
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

```

## `app/metrics.py`

```python
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

```

## `app/simulator.py`

```python
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


class FakeLLMSimulator:
    """A small fake LLM client used to generate demo traffic and metrics."""

    def generate(self, *, provider: str, model: str, prompt: str, max_output_tokens: int) -> SimulationResult:
        pricing = MODEL_PRICING_PER_1K_TOKENS.get((provider, model), DEFAULT_PRICING)

        # Very rough token estimate for demo purposes.
        input_tokens = max(1, len(prompt.split()) * random.randint(2, 5))
        output_tokens = random.randint(max(8, max_output_tokens // 4), max_output_tokens)

        latency_seconds = round(random.uniform(0.08, 2.8), 3)
        time.sleep(latency_seconds)

        # Inject a small failure rate so dashboards show errors.
        if random.random() < 0.12:
            raise LLMProviderError(f"Simulated provider failure for {provider}/{model}")

        estimated_cost_usd = round(
            ((input_tokens / 1000) * pricing["input"]) + ((output_tokens / 1000) * pricing["output"]),
            8,
        )

        response_text = (
            f"Fake response from {provider}/{model}. "
            f"Processed prompt with {input_tokens} input tokens and generated {output_tokens} output tokens."
        )

        return SimulationResult(
            text=response_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=estimated_cost_usd,
            latency_seconds=latency_seconds,
        )

```

## `app/main.py`

```python
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

```

## `app/routes/health.py`

```python
from fastapi import APIRouter

from app.config import settings
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
    )

```

## `app/routes/chat.py`

```python
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

```
