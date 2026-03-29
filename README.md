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
