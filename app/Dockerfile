FROM python:2.7-slim

# Debian Buster is EOL — point apt at the archive mirror
RUN sed -i 's|deb.debian.org|archive.debian.org|g' /etc/apt/sources.list && \
    sed -i 's|security.debian.org|archive.debian.org|g' /etc/apt/sources.list && \
    sed -i '/buster-updates/d' /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install sitecustomize.py to patch stdlib gaps (e.g. functools.lru_cache)
# before any user code runs. Must live in site-packages for auto-loading.
COPY sitecustomize.py /usr/local/lib/python2.7/site-packages/sitecustomize.py

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

# Ensure every directory under /opt/otel has __init__.py for Python 2.7.
# The upstream fix covers dirs with .py files, but some dirs (e.g. sdk/)
# only contain .pyi stubs or subdirectories and still need __init__.py.
RUN find /opt/otel -type d ! -name '__pycache__' | while read d; do \
        [ ! -f "$d/__init__.py" ] && touch "$d/__init__.py" || true; \
    done

# Fix circular import: 'from opentelemetry import metrics' fails in Python 2.7
# when called during opentelemetry.metrics initialization. Use sys.modules lookup instead.
RUN sed -i 's/^from opentelemetry import metrics$/import sys; metrics = sys.modules.get("opentelemetry.metrics")/' \
    /opt/otel/opentelemetry/metrics/_internal/instrument.py

# Fix old-style classes: Python 2.7 requires explicit (object) base for super() to work
# in multiple-inheritance MRO. Find bare class definitions and add (object).
RUN grep -rn '^class [A-Z][A-Za-z_]*:$' /opt/otel/opentelemetry/ --include='*.py' -l | \
    xargs -I{} sed -i 's/^\(class [A-Z][A-Za-z_]*\):$/\1(object):/' {}

ENV PYTHONPATH="/opt/otel"

COPY . .
RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
