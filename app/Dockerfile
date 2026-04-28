FROM python:2.7-slim

# Debian Buster is EOL — point apt at the archive mirror
RUN sed -i 's|deb.debian.org|archive.debian.org|g' /etc/apt/sources.list && \
    sed -i 's|security.debian.org|archive.debian.org|g' /etc/apt/sources.list && \
    sed -i '/buster-updates/d' /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install OpenTelemetry from the local submodule (api -> semconv -> sdk)
COPY opentelemetry-python-27/opentelemetry-api /tmp/otel/opentelemetry-api
COPY opentelemetry-python-27/opentelemetry-semantic-conventions /tmp/otel/opentelemetry-semantic-conventions
COPY opentelemetry-python-27/opentelemetry-sdk /tmp/otel/opentelemetry-sdk
RUN pip install --no-cache-dir \
    /tmp/otel/opentelemetry-api \
    /tmp/otel/opentelemetry-semantic-conventions \
    /tmp/otel/opentelemetry-sdk \
    && rm -rf /tmp/otel

# Install sitecustomize.py to patch stdlib gaps (e.g. functools.lru_cache)
# before any user code runs. Must live in site-packages for auto-loading.
COPY app/sitecustomize.py /usr/local/lib/python2.7/site-packages/sitecustomize.py
COPY app/ .
RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
