# LLM Observability Dashboard

A lightweight observability tool for LLM applications. Tracks request count, latency, token usage, estimated cost, and failures — all in a local Prometheus + Grafana stack running on Docker Compose.

---

## Why this was built

LLM APIs are opaque by default. You send a request and get a response, but you have no visibility into how much it cost, how long it took, or how often it fails — especially across multiple providers or models.

This project demonstrates how to instrument an LLM-backed API the same way you'd instrument any production service: expose metrics, collect them with Prometheus, and visualize them with Grafana.

## Problem it solves

| Problem | This project |
|---|---|
| No visibility into LLM cost | Tracks estimated USD cost per request, by model |
| No latency tracking | Records p50/p95/p99 latency via histogram |
| No failure visibility | Counts errors and computes error rate |
| Token usage is invisible | Tracks input + output tokens separately |
| Hard to compare models | All metrics are labeled by provider and model |

---

## Features

- Request count, error count, and error rate
- Latency histogram (p50, p95, p99)
- Input and output token tracking
- Estimated USD cost tracking (based on hardcoded per-1K token pricing)
- All metrics labeled by: `provider`, `model`, `endpoint`, `feature`, `status`
- Prebuilt Grafana dashboard, auto-provisioned on startup
- Simulated LLM traffic — no real API keys needed

---

## Architecture

```
HTTP Request
     │
     ▼
FastAPI app (port 8000)
  ├── /chat       → runs FakeLLMSimulator, records Prometheus metrics
  ├── /health     → health check
  └── /metrics    → Prometheus scrape endpoint
     │
     ▼
Prometheus (port 9090)
  └── scrapes /metrics every 5 seconds
     │
     ▼
Grafana (port 3000)
  └── reads from Prometheus, shows prebuilt dashboard
```

All three services run together via Docker Compose. No external dependencies.

---

## Repo structure

```
llm-observability/
├── app/
│   ├── routes/
│   │   ├── chat.py          # POST /chat — main LLM endpoint
│   │   └── health.py        # GET /health
│   ├── config.py            # App settings via environment variables
│   ├── main.py              # FastAPI app setup
│   ├── metrics.py           # Prometheus metric definitions
│   ├── schemas.py           # Pydantic request/response models
│   └── simulator.py         # Fake LLM provider (no real API calls)
├── grafana/
│   ├── dashboards/
│   │   └── llm-observability.json   # Prebuilt dashboard
│   └── provisioning/
│       ├── dashboards/dashboard.yml
│       └── datasources/datasource.yml
├── prometheus/
│   └── prometheus.yml       # Scrape config
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Setup

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose

### Run the full stack

```bash
git clone https://github.com/srimonchaari/llm-observability.git
cd llm-observability
docker compose up --build
```

Services:

| Service | URL | Credentials |
|---|---|---|
| FastAPI app | http://localhost:8000 | — |
| Prometheus | http://localhost:9090 | — |
| Grafana | http://localhost:3000 | admin / admin |

Open Grafana → Dashboards → `LLM Cost + Latency Monitor`.

### Run locally without Docker (app only)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Note: Without Docker, Prometheus and Grafana won't be running. You can still hit the API and view raw metrics at `http://localhost:8000/metrics`.

---

## Example API request

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "model": "gpt-4o-mini",
    "feature": "support-bot",
    "endpoint": "/chat",
    "prompt": "Summarize today'\''s customer issues",
    "max_output_tokens": 120
  }'
```

Example response:

```json
{
  "provider": "openai",
  "model": "gpt-4o-mini",
  "feature": "support-bot",
  "endpoint": "/chat",
  "status": "success",
  "input_tokens": 30,
  "output_tokens": 97,
  "estimated_cost_usd": 0.0000629,
  "latency_ms": 1243.0
}
```

Health check:

```bash
curl http://localhost:8000/health
```

---

## Key metrics exposed

| Metric | Type | Description |
|---|---|---|
| `llm_requests_total` | Counter | Total requests processed |
| `llm_errors_total` | Counter | Total failed requests |
| `llm_input_tokens_total` | Counter | Total input tokens consumed |
| `llm_output_tokens_total` | Counter | Total output tokens generated |
| `llm_estimated_cost_usd_total` | Counter | Cumulative estimated cost in USD |
| `llm_request_latency_seconds` | Histogram | Request latency (buckets from 50ms to 21s) |

All metrics carry labels: `provider`, `model`, `endpoint`, `feature`, `status`.

---

## Sample PromQL queries

**Error rate over time:**

```promql
sum(rate(llm_errors_total[5m])) / sum(rate(llm_requests_total[5m]))
```

**p95 latency by model:**

```promql
histogram_quantile(0.95,
  sum(rate(llm_request_latency_seconds_bucket[5m])) by (le, model)
)
```

**Estimated cost rate by model:**

```promql
sum by (model) (rate(llm_estimated_cost_usd_total[5m]))
```

**Token usage rate (input + output):**

```promql
sum(rate(llm_input_tokens_total[5m])) + sum(rate(llm_output_tokens_total[5m]))
```

---

## Dashboard overview

The prebuilt Grafana dashboard includes:

- **Request rate** — requests per second over time
- **Error rate** — percentage of failed requests
- **p95 latency** — 95th percentile response time, by model
- **Token usage** — input and output token rates
- **Estimated cost** — USD cost rate over time, by model
- **Errors by model** — which model/provider is failing most

The dashboard is provisioned automatically when the stack starts. No manual setup needed in Grafana.

---

## What is Prometheus? What is Grafana?

If you haven't used these tools before, here's the short version:

**Prometheus** is a metrics collection system. Your application exposes a `/metrics` endpoint with numbers (counters, histograms, gauges). Prometheus scrapes that endpoint on a schedule and stores the data as time series — each metric value with a timestamp and labels.

**Grafana** is a visualization tool. It connects to Prometheus as a data source and turns those time series into charts and dashboards. You write queries in PromQL (Prometheus Query Language) to select and aggregate metrics.

**How they work together in this project:**

```
FastAPI /metrics  →  Prometheus scrapes every 5s  →  Grafana reads Prometheus  →  Dashboard
```

You don't need to configure this manually. Docker Compose wires everything together, and Grafana auto-provisions both the datasource and the dashboard on startup.

---

## Limitations

- **Simulated data only.** The `/chat` endpoint does not call any real LLM provider. Responses are generated by a local simulator.
- **Estimated cost.** Pricing is hardcoded in `app/simulator.py` based on approximate per-1K token rates. These are not exact and can drift as providers change pricing.
- **No persistence.** Prometheus stores metrics in memory by default. Data resets when the container restarts.
- **No auth.** Grafana runs with default credentials (`admin`/`admin`). Do not expose this setup publicly.
- **Token estimation is approximate.** Input token count is estimated from word count, not from a real tokenizer.

### Why simulated data?

Using a simulator means the demo works without any API keys, avoids real costs, and lets you inject failure scenarios deterministically. The observability patterns — metrics, labels, dashboards — are identical to what you'd use with a real provider.

---

## Roadmap / future improvements

- [ ] Real provider integrations (OpenAI, Anthropic, Gemini)
- [ ] Automatic middleware to track every endpoint without per-route instrumentation
- [ ] Structured logging with request IDs
- [ ] Distributed tracing via OpenTelemetry
- [ ] Prometheus alerting rules (cost spikes, latency regressions, error budgets)
- [ ] Per-tenant or per-project metric labels
- [ ] Daily cost rollups and budget threshold alerts
- [ ] Load testing scripts for sustained traffic simulation
- [ ] Unit and integration test coverage

---

## Skills demonstrated

- FastAPI API design and middleware patterns
- Prometheus instrumentation (counters, histograms, labels)
- PromQL for aggregations and rate calculations
- Grafana dashboard design and auto-provisioning
- Docker Compose multi-service orchestration
- Pydantic v2 for request/response validation
- Simulated observability without external dependencies
