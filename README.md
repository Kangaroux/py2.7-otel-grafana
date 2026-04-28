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
GET  /api/products/       -- list products
POST /api/products/       -- create product  {"name": "...", "price": "..."}
GET  /api/orders/         -- list orders
POST /api/orders/         -- create order    {"product_id": ..., "quantity": ...}
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
