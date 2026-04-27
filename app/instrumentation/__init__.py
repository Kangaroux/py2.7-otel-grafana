from __future__ import absolute_import, print_function, unicode_literals

import os
import functools

from opentelemetry import trace

_initialized = False


def setup_otel():
    global _initialized
    if _initialized:
        return
    _initialized = True

    # SDK imports are deferred to here to avoid a circular import between
    # opentelemetry.sdk.trace and opentelemetry.metrics on Python 2.7.
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    from instrumentation.exporter import OTLPJsonSpanExporter
    from instrumentation.db import patch_db_tracing

    resource = Resource.create({"service.name": "django-otel-poc"})
    provider = TracerProvider(resource=resource)

    endpoint = os.environ.get("OTEL_EXPORTER_ENDPOINT", "http://alloy:4318") + "/v1/traces"
    exporter = OTLPJsonSpanExporter(endpoint=endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)
    patch_db_tracing()
    print("OpenTelemetry initialized - exporting to: " + endpoint)


def trace_function(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        _tracer = trace.get_tracer(func.__module__)
        with _tracer.start_as_current_span(func.__name__) as span:
            return func(*args, **kwargs)
    return wrapper
