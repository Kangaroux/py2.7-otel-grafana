# py2.7-otel-grafana

OpenTelemetry tracing for a Python 2.7 Django application, with a Grafana observability stack.

## Architecture

```
Django (Python 2.7) --[OTLP/JSON HTTP]--> Grafana Alloy --> Grafana Tempo
                                               |
                                               +--> Prometheus
                                                        |
                                          Grafana <-----+
```

- **Django app** -- Python 2.7, Django 1.11, with custom OTel instrumentation (request middleware, DB tracing, manual spans)
- **Grafana Alloy** -- receives OTLP traces, generates span metrics, forwards to Tempo and Prometheus
- **Grafana Tempo** -- distributed trace storage
- **Prometheus** -- stores span metrics (request rate, latency histograms)
- **Grafana** -- dashboards with auto-provisioned Tempo + Prometheus datasources

## OpenTelemetry

The OTel library is sourced from the `opentelemetry-python-27` git submodule (a fork of `opentelemetry-python` backported to Python 2.7). During Docker builds, the API, semantic-conventions, and SDK packages are installed directly from the submodule.

A `sitecustomize.py` polyfill layer provides the Python 3 stdlib features the SDK expects (`time.time_ns`, `functools.lru_cache`, `types.MappingProxyType`, etc.).

## Quick start

```bash
git clone --recurse-submodules <repo-url>
docker compose up --build
```

- App: http://localhost:8000
- Grafana: http://localhost:3000 (admin/admin)
- Tempo: http://localhost:3200
- Prometheus: http://localhost:9090

### API endpoints

```
GET  /api/products/         -- list products (seeded on first boot)
GET  /api/products/<id>/    -- get a single product
GET  /api/orders/           -- list orders
POST /api/orders/create/    -- create order  {"product_id": ..., "quantity": ..., "notes": "..."}
```

## End-to-end test

The script below starts the stack, generates some traffic, waits for the
observability pipeline to flush, then queries Tempo and Prometheus for results.

```bash
#!/usr/bin/env bash
set -euo pipefail

cleanup() { docker compose down -v; }
trap cleanup EXIT

echo "==> Building and starting the stack..."
docker compose up --build -d

echo "==> Waiting for the app..."
for i in $(seq 1 30); do
  curl -sf http://localhost:8000/ >/dev/null 2>&1 && break
  [ "$i" -eq 30 ] && { echo "App failed to start"; docker compose logs app; exit 1; }
  sleep 2
done
echo "    App is ready."

echo "==> Generating API traffic..."
curl -s http://localhost:8000/api/products/
curl -s http://localhost:8000/api/products/1/
curl -s -X POST http://localhost:8000/api/orders/create/ \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2, "notes": "e2e test"}'
curl -s -X POST http://localhost:8000/api/orders/create/ \
  -H "Content-Type: application/json" \
  -d '{"product_id": 2, "quantity": 1}'
curl -s http://localhost:8000/api/orders/
echo

echo "==> Waiting 30s for traces to flush and metrics to be scraped..."
sleep 30

echo "==> Tempo traces:"
curl -s 'http://localhost:3200/api/search?tags=service.name%3Ddjango-otel-poc' | python3 -m json.tool

echo "==> Prometheus span metrics:"
curl -s 'http://localhost:9090/api/v1/query?query=traces_spanmetrics_calls_total{service_name="django-otel-poc"}' \
  | python3 -m json.tool

echo "==> Done."
```

## Project structure

```
app/                          Django application
  instrumentation/            OTel setup, middleware, DB tracing, custom exporter
  api/                        REST views and models
  myproject/                  Django project settings
  sitecustomize.py            Python 2.7 polyfills
config/                       Grafana stack configuration (Alloy, Tempo, Prometheus, Grafana)
opentelemetry-python-27/      OTel Python SDK submodule (Python 2.7 backport)
```
