# services/auth_service.py
import httpx
from typing import Optional, Tuple
from models.auth_models import User
import logging
import time
import jwt
from jwt import PyJWTError as JWTError

logger = logging.getLogger(__name__)

class DoriotAuthService:
    # Maximum number of entries in each cache
    MAX_CACHE_SIZE = 1000

    def __init__(self, base_url: str = "https://doriot.ai"):
        self.base_url = base_url
        self.verify_url = f"{base_url}/api/me/"
        self.refresh_url = f"{base_url}/api/token/refresh/"
        self.health_url = f"{base_url}/api/health/"
        self._user_cache = {}  # Simple in-memory cache
        self._token_cache = {}  # Cache for validated tokens

    async def verify_token(self, token: str) -> Optional[User]:
        """Verify token and return user data"""
        try:
            # Check cache first
            cached_user = self._get_from_cache(token)
            if cached_user:
                logger.debug("User found in cache")
                return cached_user

            # First try local validation
            is_valid, payload = self._validate_token_locally(token)
            if not is_valid:
                logger.debug("Token validation failed locally")
                return None

            # If token is valid but user not in cache, fetch from Django
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.verify_url,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    user = User(**user_data)
                    self._add_to_cache(token, user)
                    return user
                
                logger.warning(f"User verification failed with status {response.status_code}")
                return None

        except httpx.TimeoutException:
            logger.error("Timeout while verifying token with Django backend")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}", exc_info=True)
            return None
        
    async def refresh_token(self, refresh_token: str) -> Optional[str]:
        """Refresh an expired access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.refresh_url,
                    json={"refresh": refresh_token},
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json().get("access")
                logger.warning(f"Token refresh failed with status {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}", exc_info=True)
            return None

    def _validate_token_locally(self, token: str) -> Tuple[bool, Optional[dict]]:
        """Validate JWT token locally"""
        try:
            # Basic format validation
            parts = token.split('.')
            if len(parts) != 3:
                logger.warning("Invalid token format")
                return False, None

            # Check token cache first
            if token in self._token_cache:
                cached_validation = self._token_cache[token]
                if cached_validation['exp'] > time.time():
                    return True, cached_validation['payload']

            # Decode and validate token
            payload = jwt.decode(
                token,
                options={
                    "verify_signature": False,  # Skip signature verification
                    "verify_exp": True,         # Check expiration
                    "verify_iat": True          # Check issued at
                }
            )
            
            # Check if token is expired
            exp = payload.get('exp', 0)
            if exp < time.time():
                logger.debug("Token has expired")
                return False, None

            # Cache validation result
            self._token_cache[token] = {
                'exp': exp,
                'payload': payload
            }
            
            return True, payload

        except JWTError as e:
            logger.warning(f"JWT validation error: {str(e)}")
            return False, None
        except Exception as e:
            logger.error(f"Unexpected error during token validation: {str(e)}")
            return False, None

    def _get_from_cache(self, token: str) -> Optional[User]:
        """Get user from cache if token is still valid"""
        cached_data = self._user_cache.get(token)
        if cached_data:
            if cached_data['exp'] > time.time():
                return cached_data['user']
            else:
                del self._user_cache[token]
                logger.debug("Removed expired user from cache")
        return None

    def _cleanup_cache(self):
        """Remove expired entries from caches and enforce size limits"""
        current_time = time.time()
        
        # Clean expired entries
        expired_users = [
            token for token, data in self._user_cache.items()
            if data['exp'] < current_time
        ]
        for token in expired_users:
            del self._user_cache[token]
            
        expired_tokens = [
            token for token, data in self._token_cache.items()
            if data['exp'] < current_time
        ]
        for token in expired_tokens:
            del self._token_cache[token]

        # Enforce size limits
        if len(self._user_cache) > self.MAX_CACHE_SIZE:
            sorted_entries = sorted(
                self._user_cache.items(),
                key=lambda x: x[1]['exp']
            )
            for token, _ in sorted_entries[:len(self._user_cache) - self.MAX_CACHE_SIZE]:
                del self._user_cache[token]
                logger.debug("Removed oldest user from cache due to size limit")

        if len(self._token_cache) > self.MAX_CACHE_SIZE:
            sorted_entries = sorted(
                self._token_cache.items(),
                key=lambda x: x[1]['exp']
            )
            for token, _ in sorted_entries[:len(self._token_cache) - self.MAX_CACHE_SIZE]:
                del self._token_cache[token]
                logger.debug("Removed oldest token from cache due to size limit")

    def _add_to_cache(self, token: str, user: User):
        """Add user to cache with expiration"""
        try:
            # Cleanup before adding new entries
            self._cleanup_cache()
            
            payload = jwt.decode(token, options={"verify_signature": False})
            exp = payload.get('exp', time.time() + 3600)
            self._user_cache[token] = {
                'user': user,
                'exp': exp
            }
            logger.debug("Added user to cache")
        except JWTError:
            logger.warning("Failed to add user to cache - invalid token")
            pass

    async def healthcheck(self) -> bool:
        """Check if auth service is accessible"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.health_url,
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Auth service healthcheck failed: {str(e)}")
            return False