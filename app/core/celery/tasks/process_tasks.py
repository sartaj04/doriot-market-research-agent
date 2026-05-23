from core.celery.config import celery_app
from core.redis.client import get_redis_client
from core.redis.client import get_redis_client

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=300
)
async def process_token_usage(self, user_id: str, token_count: int):
    """Async task to process token usage"""
    try:
        from services.token_service import TokenService  # Import inside function to avoid circular import
        redis_client = get_redis_client()
        token_service = TokenService(redis_client)
        await token_service.update_usage(user_id, token_count)
    except Exception as exc:
        self.retry(exc=exc)