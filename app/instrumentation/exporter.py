from __future__ import absolute_import, print_function, unicode_literals

import json
import logging

import requests
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

logger = logging.getLogger(__name__)


class OTLPJsonSpanExporter(SpanExporter):

    def __init__(self, endpoint="http://alloy:4318/v1/traces"):
        super(OTLPJsonSpanExporter, self).__init__()
        self.endpoint = endpoint
        self._session = requests.Session()

    def export(self, spans):
        if not spans:
            return SpanExportResult.SUCCESS
        try:
            payload = self._build_payload(spans)
            response = self._session.post(
                self.endpoint,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            if response.status_code < 400:
                return SpanExportResult.SUCCESS
            else:
                logger.error(
                    "OTLP export failed: %s %s",
                    response.status_code,
                    response.text,
                )
                return SpanExportResult.FAILURE
        except Exception:
            logger.exception("OTLP export error")
            return SpanExportResult.FAILURE

    def shutdown(self):
        self._session.close()

    def force_flush(self, timeout_millis=None):
        return True

    def _build_payload(self, spans):
        resource_map = {}
        for span in spans:
            res_key = id(span.resource)
            if res_key not in resource_map:
                resource_map[res_key] = {
                    "resource": span.resource,
                    "scopes": {},
                }

            scope = None
            if hasattr(span, 'instrumentation_info'):
                scope = span.instrumentation_info
            elif hasattr(span, 'instrumentation_scope'):
                scope = span.instrumentation_scope

            scope_key = scope.name if scope else ""
            if scope_key not in resource_map[res_key]["scopes"]:
                resource_map[res_key]["scopes"][scope_key] = {
                    "scope": scope,
                    "spans": [],
                }
            resource_map[res_key]["scopes"][scope_key]["spans"].append(span)

        resource_spans = []
        for res_data in resource_map.values():
            scope_spans = []
            for scope_data in res_data["scopes"].values():
                scope_obj = scope_data["scope"]
                scope_name = ""
                scope_version = ""
                if scope_obj is not None:
                    scope_name = scope_obj.name if hasattr(scope_obj, 'name') else ""
                    scope_version = scope_obj.version if hasattr(scope_obj, 'version') else ""

                scope_spans.append({
                    "scope": {
                        "name": scope_name,
                        "version": scope_version,
                    },
                    "spans": [self._format_span(s) for s in scope_data["spans"]],
                })

            resource_obj = res_data["resource"]
            resource_attrs = {}
            if resource_obj is not None and hasattr(resource_obj, 'attributes'):
                resource_attrs = resource_obj.attributes

            resource_spans.append({
                "resource": {
                    "attributes": self._format_attributes(resource_attrs),
                },
                "scopeSpans": scope_spans,
            })

        return {"resourceSpans": resource_spans}

    def _format_span(self, span):
        parent_id = ""
        if span.parent is not None:
            parent_id = self._format_span_id(span.parent.span_id)

        result = {
            "traceId": self._format_trace_id(span.context.trace_id),
            "spanId": self._format_span_id(span.context.span_id),
            "parentSpanId": parent_id,
            "name": span.name,
            "kind": self._get_span_kind(span.kind),
            "startTimeUnixNano": str(span.start_time),
            "endTimeUnixNano": str(span.end_time),
            "attributes": self._format_attributes(span.attributes or {}),
            "status": self._format_status(span.status),
        }

        if span.events:
            result["events"] = [self._format_event(e) for e in span.events]

        return result

    def _format_event(self, event):
        result = {
            "name": event.name,
            "timeUnixNano": str(event.timestamp),
        }
        if event.attributes:
            result["attributes"] = self._format_attributes(event.attributes)
        return result

    def _format_status(self, status):
        code = 0
        if status and status.status_code is not None:
            if hasattr(status.status_code, 'value'):
                code = status.status_code.value
            else:
                code = int(status.status_code)
        result = {"code": code}
        if status and status.description:
            result["message"] = status.description
        return result

    def _format_trace_id(self, trace_id):
        return format(trace_id, '032x')

    def _format_span_id(self, span_id):
        return format(span_id, '016x')

    def _get_span_kind(self, kind):
        # SDK enum: INTERNAL=0, SERVER=1, CLIENT=2, PRODUCER=3, CONSUMER=4
        # OTLP wire: INTERNAL=1, SERVER=2, CLIENT=3, PRODUCER=4, CONSUMER=5
        if hasattr(kind, 'value'):
            val = kind.value
        else:
            val = int(kind)
        return val + 1

    def _format_attributes(self, attributes):
        result = []
        items = []
        if hasattr(attributes, 'items'):
            items = attributes.items()
        for key, value in items:
            result.append({
                "key": str(key),
                "value": self._format_value(value),
            })
        return result

    def _format_value(self, value):
        if isinstance(value, bool):
            return {"boolValue": value}
        elif isinstance(value, int):
            return {"intValue": str(value)}
        elif isinstance(value, float):
            return {"doubleValue": value}
        else:
            return {"stringValue": str(value)}
