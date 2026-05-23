# Add to monitoring/metrics.py
from prometheus_client import Counter, Histogram

WS_CONNECTIONS = Counter(
    'ws_connections_total',
    'Total WebSocket connections'
)

REDIS_OPERATIONS = Counter(
    'redis_operations_total',
    'Total Redis operations',
    ['operation']
)

CELERY_TASKS = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status']
)