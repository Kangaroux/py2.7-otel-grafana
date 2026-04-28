#!/usr/bin/env bash
set -euo pipefail

echo "==> Building and starting the stack..."
docker compose up --quiet-build --build -d

echo "==> Waiting for the app..."
for i in $(seq 1 30); do
  curl -sf http://localhost:8000/ >/dev/null 2>&1 && break
  [ "$i" -eq 30 ] && { echo "App failed to start"; docker compose logs app; exit 1; }
  sleep 1
done
echo "    App is ready."
echo

existing_orders=$(curl -s http://localhost:8000/api/orders/ | jq -r '.orders | length')
if [[ $existing_orders != 0 ]]; then
  echo "WARNING: there is existing order data. The e2e script needs a clean DB to run."
  read -p "Run 'docker compose down -v'? [y/N] " ans
  if [[ $ans != 'y' ]]; then
    exit 0
  fi
  docker compose down -v
  echo
  echo "Please re-run $0"
  exit 0
fi

do_curl() {
  echo ">>> curl $@"
  curl "$@" | jq .
  echo
}

echo "==> Generating API traffic..."
echo
do_curl -s http://localhost:8000/api/products/
do_curl -s -X POST http://localhost:8000/api/orders/create/ \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2, "notes": "e2e test"}'
do_curl -s -X POST http://localhost:8000/api/orders/create/ \
  -H "Content-Type: application/json" \
  -d '{"product_id": 2, "quantity": 1}'
do_curl -s http://localhost:8000/api/orders/

waittime=30
echo "==> Waiting ${waittime}s for traces to flush and metrics to be scraped..."
sleep $waittime

echo "==> Tempo traces:"
curl -s 'http://localhost:3200/api/search?limit=5' | jq .

echo "==> Prometheus span metrics:"
curl -s 'http://localhost:9090/api/v1/query?query=traces_spanmetrics_calls_total' | jq .

echo "==> Done."

