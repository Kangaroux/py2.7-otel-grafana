FROM python:2.7-slim

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Clone OTel Python library (python27 branch)
RUN git clone --branch python27 --depth 1 https://github.com/Kangaroux/opentelemetry-python.git /opt/otel-python

# Merge OTel package sources into a single directory.
# We can't use pip install because the packages use hatchling (requires Python 3.7+).
# Instead, copy the src/ trees directly — the opentelemetry namespace merges cleanly
# since each package contributes distinct sub-packages (trace/, sdk/, semconv/).
RUN mkdir -p /opt/otel && \
    cp -r /opt/otel-python/opentelemetry-semantic-conventions/src/* /opt/otel/ && \
    cp -r /opt/otel-python/opentelemetry-sdk/src/* /opt/otel/ && \
    cp -r /opt/otel-python/opentelemetry-api/src/* /opt/otel/

ENV PYTHONPATH="/opt/otel"

COPY . .
RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
