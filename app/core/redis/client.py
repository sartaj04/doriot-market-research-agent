import redis.asyncio as redis
from typing import Optional
import logging
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class RedisClient:
    _instance: Optional[redis.Redis] = None

    @classmethod
    async def get_instance(cls) -> redis.Redis:
        if cls._instance is None:
            cls._instance = await cls._create_client()
        return cls._instance

    @classmethod
    async def _create_client(cls) -> redis.Redis:
        try:
            client = redis.Redis(
                host=settings.REDIS_PRODUCTION_HOST if settings.ENVIRONMENT == "production" else settings.REDIS_LOCAL_HOST,
                port=settings.REDIS_PRODUCTION_PORT if settings.ENVIRONMENT == "production" else settings.REDIS_LOCAL_PORT,
                ssl=settings.REDIS_PRODUCTION_SSL if settings.ENVIRONMENT == "production" else False,
                ssl_cert_reqs=None if settings.REDIS_PRODUCTION_SSL and settings.ENVIRONMENT == "production" else None,
                decode_responses=True
            )
            # Test connection
            await client.ping()
            logger.info(f"Successfully connected to Redis at {client.connection_pool.connection_kwargs['host']}")
            return client
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise

async def get_redis_client() -> redis.Redis:
    return await RedisClient.get_instance()

async def check_redis_health() -> bool:
    try:
        client = await get_redis_client()
        return await client.ping()
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return False