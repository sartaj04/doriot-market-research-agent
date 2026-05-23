from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import sys
import json
import time
from core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.debug = settings.DEBUG

    async def dispatch(self, request: Request, call_next):
        if not self.debug:
            logger.debug("Debug mode is off, skipping detailed logging")
            return await call_next(request)

        logger.debug("Processing request with detailed logging")

        start_time = time.time()
        
        # Log detailed request info only in debug mode
        logger.debug(f"\n{'='*50}")
        logger.debug(f"Request: {request.method} {request.url.path}")
        logger.debug(f"Headers: {dict(request.headers)}")
        
        # Log request body for POST/PUT
        if request.method in ['POST', 'PUT']:
            try:
                body = await request.body()
                if body:
                    try:
                        json_body = json.loads(body)
                        logger.debug(f"Request body: {json.dumps(json_body, indent=2)}")
                    except json.JSONDecodeError:
                        logger.debug(f"Request body (raw): {body.decode()}")
            except Exception as e:
                logger.error(f"Error reading request body: {str(e)}")
        
        try:
            response = await call_next(request)
            
            if self.debug:
                process_time = time.time() - start_time
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Process time: {process_time:.3f}s")
                logger.debug(f"{'='*50}\n")
            
            return response
            
        except Exception as exc:
            logger.exception("Error processing request:")
            raise