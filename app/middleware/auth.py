from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt
from core.config import get_settings
from services.auth_service import DoriotAuthService
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, auth_service: DoriotAuthService = None):
        super().__init__(app)
        self.auth_service = auth_service or DoriotAuthService()

    async def dispatch(self, request: Request, call_next):
        current_path = request.url.path

        # Skip authentication for public paths
        if self._is_public_path(current_path):
            return await call_next(request)

        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                raise HTTPException(
                    status_code=401,
                    detail="Missing authentication token"
                )

            token = auth_header.split(' ')[1]
            user = await self.auth_service.verify_token(token)
            
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid or expired token"
                )

            # Set user in request state
            request.state.user = user
            request.state.user_id = user.uuid
            
            return await call_next(request)

        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Auth error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Authentication error"
            )

    def _is_public_path(self, path: str) -> bool:
        """Check if path is public"""
        public_paths = [
            "/favicon.ico",
            "/docs",
            "/redoc",
            "/openapi.json",
            f"{settings.API_V1_STR}/openapi.json",
            "/metrics",
            f"{settings.API_V1_STR}/health",
            f"{settings.API_V1_STR}/health/",
            "/static",
            "/_next",
            f"{settings.API_V1_STR}/startup",  # Add this line for startup registration
            f"{settings.API_V1_STR}/startup/", 
        ]
        return any(path.startswith(p) for p in public_paths)