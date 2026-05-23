from prometheus_client import Counter, Histogram
import time

# Metrics
REQUEST_COUNT = Counter(
    'request_count',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'request_latency_seconds',
    'Request latency in seconds',
    ['method', 'endpoint']
)

TOKEN_USAGE = Counter(
    'token_usage_total',
    'Total token usage',
    ['user_id']
)
