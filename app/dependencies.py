
# app/dependencies.py
from typing import Generator
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from core.config import settings
from core.redis.client import get_redis_client
from core.database import SessionLocal
from models.auth_models import User


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(request: Request) -> User:
    """Get current authenticated user from request state"""
    if not hasattr(request.state, 'user'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return request.state.user

async def get_current_user_id(request: Request) -> str:
    """Get current user ID from request state"""
    user = await get_current_user(request)
    return user.uuid

async def get_redis():
    return await get_redis_client()