# Add to routes/health.py
from fastapi import APIRouter, Depends, Request
from core.redis.client import check_redis_health
from core.celery.worker import check_celery_health

router = APIRouter()

# @router.get("/health")
# async def health_check(request: Request):
#     return {
#         "redis": await check_redis_health(),
#         "celery": await check_celery_health(),
#         "websocket": len(request.app.state.chat_ws.active_connections) >= 0
#     }
@router.get("/health")
async def health_check(request: Request):
    celery_health = await check_celery_health()
    redis_health = await check_redis_health()
    ws_health = len(request.app.state.chat_ws.active_connections) >= 0
    
    # Consider "unknown" Celery status as healthy in cluster mode
    celery_ok = celery_health.get("status") in ["healthy", "unknown"]
    
    return {
        "redis": redis_health,
        "celery": celery_health,
        "websocket": ws_health,
        "status": "healthy" if (redis_health and celery_ok and ws_health) else "unhealthy"
    }