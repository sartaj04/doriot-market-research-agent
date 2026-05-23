from datetime import datetime, timedelta
from redis.asyncio import Redis
from typing import Dict
from models.auth_models import User

class TokenService:
    def __init__(
        self,
        redis_client: Redis,
        daily_limit: int,
        total_limit: int,
        user: User = None
    ):
        self.redis = redis_client
        self.daily_limit = daily_limit
        self.total_limit = total_limit
        self.user = user

    async def check_limits(self, user_id: str) -> bool:
        """Check if user has exceeded token limits"""
        daily_usage = await self.get_daily_usage(user_id)
        
        if self.user and self.user.is_payment_done:
            monthly_usage = await self.get_monthly_usage(user_id)
            return daily_usage < self.daily_limit and monthly_usage < self.total_limit
        else:
            total_usage = await self.get_total_usage(user_id)
            return daily_usage < self.daily_limit and total_usage < self.total_limit

    async def update_usage(self, user_id: str, token_count: int) -> None:
        """Update token usage for user"""
        # Update daily usage
        daily_key = f"daily_tokens:{user_id}"
        await self.redis.incrby(daily_key, token_count)
        
        # Set expiry for daily tokens
        tomorrow = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)
        await self.redis.expireat(daily_key, tomorrow)
        
        if self.user and self.user.is_payment_done:
            # Update monthly usage for paid users
            monthly_key = f"monthly_tokens:{user_id}"
            await self.redis.incrby(monthly_key, token_count)
            
            # Set expiry for next month's first day
            first_of_next_month = (datetime.now().replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            ) + timedelta(days=32)).replace(day=1)
            await self.redis.expireat(monthly_key, first_of_next_month)
        else:
            # Update permanent total usage for free users
            total_key = f"total_tokens:{user_id}"
            await self.redis.incrby(total_key, token_count)

    async def get_daily_usage(self, user_id: str) -> int:
        """Get daily token usage"""
        daily_key = f"daily_tokens:{user_id}"
        value = await self.redis.get(daily_key)
        return int(value or 0)

    async def get_monthly_usage(self, user_id: str) -> int:
        """Get monthly token usage for paid users"""
        monthly_key = f"monthly_tokens:{user_id}"
        value = await self.redis.get(monthly_key)
        return int(value or 0)

    async def get_total_usage(self, user_id: str) -> int:
        """Get total token usage for free users"""
        total_key = f"total_tokens:{user_id}"
        value = await self.redis.get(total_key)
        return int(value or 0)

    async def get_usage_stats(self, user_id: str) -> Dict:
        """Get complete usage statistics"""
        stats = {
            "daily_tokens": await self.get_daily_usage(user_id),
            "daily_limit": self.daily_limit,
            "total_limit": self.total_limit,
            "is_paid_user": self.user and self.user.is_payment_done if self.user else False
        }
        
        if self.user and self.user.is_payment_done:
            stats["monthly_tokens"] = await self.get_monthly_usage(user_id)
        else:
            stats["total_tokens"] = await self.get_total_usage(user_id)
            
        return stats