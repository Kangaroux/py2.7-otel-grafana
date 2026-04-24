from __future__ import absolute_import, print_function, unicode_literals

from opentelemetry import trace, context
from opentelemetry.trace import SpanKind, StatusCode, Status
from django.utils.deprecation import MiddlewareMixin


class OpenTelemetryMiddleware(MiddlewareMixin):

    def __init__(self, get_response=None):
        super(OpenTelemetryMiddleware, self).__init__(get_response)
        self.tracer = trace.get_tracer("django.request")

    def process_request(self, request):
        route = request.path
        try:
            from django.core.urlresolvers import resolve
            match = resolve(request.path)
            if match.url_name:
                route = match.url_name
        except Exception:
            pass

        span = self.tracer.start_span(
            name="{0} {1}".format(request.method, route),
            kind=SpanKind.SERVER,
        )
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", request.build_absolute_uri())
        span.set_attribute("http.target", request.path)
        span.set_attribute("http.route", route)
        span.set_attribute("http.scheme", request.scheme)

        ctx = trace.set_span_in_context(span)
        token = context.attach(ctx)
        request._otel_span = span
        request._otel_token = token

    def process_response(self, request, response):
        span = getattr(request, '_otel_span', None)
        token = getattr(request, '_otel_token', None)
        if span is not None:
            span.set_attribute("http.status_code", response.status_code)
            if response.status_code >= 500:
                span.set_status(Status(StatusCode.ERROR))
            span.end()
        if token is not None:
            context.detach(token)
        return response

    def process_exception(self, request, exception):
        span = getattr(request, '_otel_span', None)
        if span is not None:
            span.set_status(Status(StatusCode.ERROR, str(exception)))
            span.record_exception(exception)
