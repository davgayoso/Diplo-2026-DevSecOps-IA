from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Histogram
from prometheus_client.exposition import generate_latest


class Metrics:
    content_type = CONTENT_TYPE_LATEST

    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        self.http_requests = Counter(
            "rag_api_http_requests_total",
            "Total HTTP requests handled by the API.",
            ("method", "path", "status_code"),
            registry=self.registry,
        )
        self.http_duration = Histogram(
            "rag_api_http_request_duration_seconds",
            "HTTP request duration in seconds.",
            ("method", "path"),
            registry=self.registry,
        )
        self.rate_limit_blocks = Counter(
            "rag_api_rate_limit_blocks_total",
            "Requests blocked by the in-memory rate limiter.",
            ("client_id",),
            registry=self.registry,
        )

    def observe_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        self.http_requests.labels(method, path, str(status_code)).inc()
        self.http_duration.labels(method, path).observe(duration_seconds)

    def record_rate_limit_block(self, client_id: str) -> None:
        self.rate_limit_blocks.labels(client_id).inc()

    def render(self) -> bytes:
        return generate_latest(self.registry)
