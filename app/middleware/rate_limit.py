from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from services.token_service import TokenService
from core.config import get_settings
from redis.asyncio import Redis
import logging
from typing import Optional

logger = logging.getLogger(__name__)
settings = get_settings()

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_client):
        super().__init__(app)
        self.get_redis = redis_client
        self._token_service: Optional[TokenService] = None
        self._redis_client: Optional[Redis] = None

    async def _init_token_service(self) -> None:
        """Initialize token service if not already initialized"""
        if self._token_service is None:
            try:
                if self._redis_client is None:
                    self._redis_client = await self.get_redis()
                if not self._redis_client:
                    raise RuntimeError("Failed to initialize Redis client")
                
                self._token_service = TokenService(
                    self._redis_client,
                    settings.DAILY_TOKEN_LIMIT,
                    settings.TOTAL_TOKEN_LIMIT
                )
            except Exception as e:
                logger.error(f"Failed to initialize token service: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail="Error initializing rate limiting service"
                )

    async def dispatch(self, request: Request, call_next):
        """Handle rate limiting for requests"""
        # Skip middleware for non-chat endpoints
        if not request.url.path.startswith(f"{settings.API_V1_STR}/chat"):
            return await call_next(request)

        try:
            # Get user ID from request state
            user_id = getattr(request.state, "user_id", None)
            if not user_id:
                logger.debug("No user_id in request state, skipping rate limit check")
                return await call_next(request)

            # Initialize token service if needed
            await self._init_token_service()
            if not self._token_service:
                raise HTTPException(
                    status_code=500,
                    detail="Rate limiting service unavailable"
                )

            # Check rate limits
            try:
                can_proceed = await self._token_service.check_limits(user_id)
                if not can_proceed:
                    logger.warning(f"Rate limit exceeded for user: {user_id}")
                    raise HTTPException(
                        status_code=429,
                        detail="Rate limit exceeded. Please try again later.",
                        headers={"Retry-After": "3600"}
                    )
                
                # Process the request if within limits
                response = await call_next(request)

                # Update token usage on successful response
                try:
                    token_count = getattr(response, "token_count", 1)
                    await self._token_service.update_usage(user_id, token_count)
                except Exception as e:
                    logger.error(f"Error updating token usage: {str(e)}")
                
                return response

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error checking rate limits: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail="Error checking rate limits"
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in rate limit middleware: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Internal server error in rate limiting"
            )