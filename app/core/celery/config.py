from celery import Celery
from core.config import get_settings
import ssl
from core.redis.client import get_redis_client
from services.token_service import TokenService

settings = get_settings()

def create_celery_app() -> Celery:
    app = Celery(
        "market_research",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend
    )

    app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
    )

    if settings.ENVIRONMENT == "production":
        app.conf.update(
            broker_use_ssl={
                'ssl_cert_reqs': ssl.CERT_NONE
            },
            redis_backend_use_ssl={
                'ssl_cert_reqs': ssl.CERT_NONE
            },
            broker_pool_limit=None,
            broker_connection_timeout=5,
            broker_connection_retry=True,
            broker_connection_max_retries=3,
            task_acks_late=True,
            task_reject_on_worker_lost=True,
            worker_prefetch_multiplier=1
        )

    return app

celery_app = create_celery_app()

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=300
)
def process_token_usage(self, user_id: str, token_count: int):
    try:
        redis_client = get_redis_client()
        token_service = TokenService(redis_client)
        token_service.update_usage(user_id, token_count)
    except Exception as exc:
        self.retry(exc=exc)