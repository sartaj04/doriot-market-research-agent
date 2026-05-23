from core.config import settings
from core.celery.config import celery_app
import os
from typing import Dict, Any

def start_worker():
    worker_args = ['worker', '-l', 'INFO']
    
    if settings.ENVIRONMENT == "production":
        worker_args.extend([
            '--concurrency=4',
            '--max-tasks-per-child=1000',
            '--max-memory-per-child=512000',
            '--time-limit=1800',
            '--soft-time-limit=1500'
        ])
    else:
        worker_args.extend([
            '--concurrency=2',
            '--pool=solo'
        ])
    
    celery_app.worker_main(worker_args)


async def check_celery_health() -> Dict[str, Any]:
    """
    Check Celery worker health status using cluster-safe methods
    Returns a dictionary with health check results
    """
    try:
        # Create inspector with short timeout
        inspect = celery_app.control.inspect(timeout=3.0)
        
        # Get active workers using ping (cluster-safe operation)
        active_workers = inspect.ping()
        
        if active_workers:
            worker_count = len(active_workers)
            return {
                "status": "healthy",
                "workers": worker_count,
                "message": f"Found {worker_count} active worker{'s' if worker_count > 1 else ''}"
            }
        
        return {
            "status": "unhealthy",
            "workers": 0,
            "message": "No active Celery workers found"
        }
        
    except Exception as e:
        error_msg = str(e)
        # Handle common error cases
        if "SELECT" in error_msg:
            return {
                "status": "unknown",
                "message": "Health check running in cluster mode"
            }
        return {
            "status": "unhealthy",
            "message": f"Health check failed: {error_msg}"
        }


if __name__ == '__main__':
    start_worker()