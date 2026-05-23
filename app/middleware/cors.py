from fastapi.middleware.cors import CORSMiddleware
from core.config import settings

def setup_cors_middleware(app):
    # app.add_middleware(
    #     CORSMiddleware,
    #     allow_origins=settings.ALLOWED_ORIGINS,
    #     allow_credentials=True,
    #     allow_methods=["*"],
    #     allow_headers=["*"],
    # )
    pass