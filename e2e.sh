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
curl -s 'http://localhost:3200/api/search?limit=5' | jq .

echo "==> Prometheus span metrics:"
curl -s 'http://localhost:9090/api/v1/query?query=traces_spanmetrics_calls_total' | jq .

echo "==> Done."

