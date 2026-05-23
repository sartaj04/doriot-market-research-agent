# Add to core/exceptions.py
class ServiceException(Exception):
    """Base exception for service errors"""
    pass

class RedisConnectionError(ServiceException):
    """Redis connection error"""
    pass

class CeleryTaskError(ServiceException):
    """Celery task error"""
    pass

class WebSocketConnectionError(ServiceException):
    """WebSocket connection error"""
    pass