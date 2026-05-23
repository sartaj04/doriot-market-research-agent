from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging
from core.config import settings

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except HTTPException as exc:
            # Re-raise HTTP exceptions (they're handled by FastAPI)
            raise
        except Exception as exc:
            # Log unexpected errors
            logger.error(
                f"Unexpected error in {request.url.path}",
                exc_info=True
            )
            
            # Return 500 response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "detail": str(exc) if settings.DEBUG else None
                }
            )