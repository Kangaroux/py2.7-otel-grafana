FROM python:2.7-slim

# Debian Buster is EOL — point apt at the archive mirror
RUN sed -i 's|deb.debian.org|archive.debian.org|g' /etc/apt/sources.list && \
    sed -i 's|security.debian.org|archive.debian.org|g' /etc/apt/sources.list && \
    sed -i '/buster-updates/d' /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install OpenTelemetry from the local submodule by merging the src/ trees.
# pip wheel installs can't merge Python 2.7 namespace packages across multiple
# packages, so we copy the source directly and add it to PYTHONPATH.
COPY opentelemetry-python-27/opentelemetry-api/src/opentelemetry /opt/otel/opentelemetry
COPY opentelemetry-python-27/opentelemetry-semantic-conventions/src/opentelemetry /opt/otel/opentelemetry
COPY opentelemetry-python-27/opentelemetry-sdk/src/opentelemetry /opt/otel/opentelemetry
ENV PYTHONPATH="/opt/otel"

# Install sitecustomize.py to patch stdlib gaps (e.g. functools.lru_cache)
# before any user code runs. Must live in site-packages for auto-loading.
COPY app/sitecustomize.py /usr/local/lib/python2.7/site-packages/sitecustomize.py
COPY app/ .
RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
