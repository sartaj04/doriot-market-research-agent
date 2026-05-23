from fastapi import FastAPI
from core.config import get_settings
from routes import chat
from middleware.cors import setup_cors_middleware
from middleware.request_id import RequestIDMiddleware
from middleware.rate_limit import RateLimitMiddleware
from middleware.auth import AuthMiddleware
from middleware.error_handler import ErrorHandlerMiddleware
from middleware.logging import LoggingMiddleware
from prometheus_client import make_asgi_app
from api.docs import custom_openapi
from wbsocket_connection.chat import ChatWebSocket
from dependencies import get_redis as get_redis_client
from core.celery.config import celery_app
from routes import chat, health, auth, startup_registration
import logging
import uvicorn
from contextlib import asynccontextmanager
from services.auth_service import DoriotAuthService
import sys
from core.logging import setup_logging
# Add imports for environment variable handling
import os
from dotenv import load_dotenv

# Force reload environment variables
load_dotenv(override=True)

settings =get_settings()
setup_logging()
logger = logging.getLogger(__name__)

# Log critical settings for debugging


logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)





@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application"""
    # Startup
    logger.info("Starting up application...")
    try:
        # Initialize Redis
        redis_client = await get_redis_client()
        pong = await redis_client.ping()
        if pong:
            logger.info("Redis connection established")
            app.state.redis = redis_client
        else:
            raise RuntimeError("Redis connection failed")
            
        # Initialize WebSocket manager
        app.state.chat_ws = ChatWebSocket()
        logger.info("WebSocket manager initialized")
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    if hasattr(app.state, 'redis'):
        await app.state.redis.close()
    if hasattr(app.state, 'chat_ws'):
        await app.state.chat_ws.close_all()

def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan
    )
    
    # Setup middleware (order matters)
    app.add_middleware(LoggingMiddleware)
    setup_cors_middleware(app)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(LoggingMiddleware)
    auth_service = DoriotAuthService(base_url="https://doriot.ai")
    app.add_middleware(AuthMiddleware, auth_service=auth_service)
    # app.add_middleware(AuthMiddleware)  # Move auth middleware before rate limit
    app.add_middleware(
        RateLimitMiddleware,
        redis_client=get_redis_client
    )
    
    # Add Prometheus metrics
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    
    # Include routers
    # app.include_router(
    #     auth.router,  # Move auth router first
    #     prefix=f"{settings.API_V1_STR}/auth",
    #     tags=["auth"]
    # )
    
    app.include_router(
        chat.router,
        prefix=settings.API_V1_STR,
        tags=["chat"]
    )

    app.include_router(
        startup_registration.router,
        prefix=f"{settings.API_V1_STR}/startup",
        tags=["startup"]
    )
    
    app.include_router(
        health.router,
        prefix=f"{settings.API_V1_STR}/health",
        tags=["health"]
    )
    
    # Custom OpenAPI schema
    app.openapi = lambda: custom_openapi(app)
    
    return app

app = create_application()

if __name__ == "__main__":

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8008,
        reload=settings.DEBUG,
        reload_dirs=["app"], 

    )