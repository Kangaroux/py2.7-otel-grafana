#!/usr/bin/env bash
set -exuo pipefail

curl -s http://localhost:8000/api/products/ > /dev/null

curl -s -X POST http://localhost:8000/api/orders/create/ \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2, "notes": "e2e test"}' > /dev/null

curl -s -X POST http://localhost:8000/api/orders/create/ \
  -H "Content-Type: application/json" \
  -d '{"product_id": 2, "quantity": 1}' > /dev/null

curl -s http://localhost:8000/api/orders/ > /dev/null
