import json
import logging

from app.observability.logging import JsonFormatter
from app.observability.metrics import Metrics


def test_json_formatter_includes_safe_request_fields() -> None:
    record = logging.LogRecord(
        name="rag_api",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request_completed",
        args=(),
        exc_info=None,
    )
    record.request_id = "request-1"
    record.status_code = 200

    payload = json.loads(JsonFormatter().format(record))

    assert payload["event"] == "request_completed"
    assert payload["request_id"] == "request-1"
    assert payload["status_code"] == 200
    assert "api_key" not in payload
    assert "question" not in payload


def test_metrics_render_requests_and_rate_limit_blocks() -> None:
    metrics = Metrics()

    metrics.observe_request("POST", "/ask", 200, 0.25)
    metrics.record_rate_limit_block("reader")
    rendered = metrics.render().decode()

    request_metric = 'rag_api_http_requests_total{method="POST",path="/ask",status_code="200"} 1.0'
    assert request_metric in rendered
    assert 'rag_api_rate_limit_blocks_total{client_id="reader"} 1.0' in rendered
