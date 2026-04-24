from __future__ import absolute_import, print_function, unicode_literals

from opentelemetry import trace
from django.db.backends.utils import CursorWrapper

_original_execute = None
_original_executemany = None


def patch_db_tracing():
    global _original_execute, _original_executemany
    _original_execute = CursorWrapper.execute
    _original_executemany = CursorWrapper.executemany
    _tracer = trace.get_tracer("django.db")

    def traced_execute(self, sql, params=None):
        with _tracer.start_as_current_span("db.query", kind=trace.SpanKind.CLIENT) as span:
            span.set_attribute("db.system", "sqlite")
            span.set_attribute("db.statement", str(sql))
            return _original_execute(self, sql, params)

    def traced_executemany(self, sql, param_list):
        with _tracer.start_as_current_span("db.query", kind=trace.SpanKind.CLIENT) as span:
            span.set_attribute("db.system", "sqlite")
            span.set_attribute("db.statement", str(sql))
            return _original_executemany(self, sql, param_list)

    CursorWrapper.execute = traced_execute
    CursorWrapper.executemany = traced_executemany
