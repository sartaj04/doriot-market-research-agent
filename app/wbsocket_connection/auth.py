# Add to websockets/auth.py
from jose import jwt
from core.config import settings
from typing import Optional

async def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub")
    except:
        return None