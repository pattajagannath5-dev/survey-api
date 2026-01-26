"""Redis client for caching."""
import redis
from app.config import settings
import json
from typing import Optional, Any

# Create Redis connection
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_keepalive=True
)


class CacheService:
    """Service for caching operations."""
    
    def __init__(self):
        self.client = redis_client
        self.default_ttl = 300  # 5 minutes
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set a value in cache."""
        try:
            ttl = ttl or self.default_ttl
            self.client.setex(key, ttl, json.dumps(value))
            return True
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        try:
            self.client.delete(key)
            return True
        except Exception:
            return False
    
    def clear_pattern(self, pattern: str) -> bool:
        """Clear all keys matching a pattern."""
        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
            return True
        except Exception:
            return False
    
    # Survey-specific cache methods
    def get_survey_analytics(self, survey_id: str) -> Optional[dict]:
        """Get cached survey analytics."""
        return self.get(f"survey_analytics:{survey_id}")
    
    def set_survey_analytics(self, survey_id: str, analytics: dict, ttl: int = 300) -> bool:
        """Cache survey analytics."""
        return self.set(f"survey_analytics:{survey_id}", analytics, ttl)
    
    def invalidate_survey_cache(self, survey_id: str) -> bool:
        """Invalidate all cache related to a survey."""
        return self.clear_pattern(f"survey_*:{survey_id}")
    
    def get_survey_list(self, cache_key: str) -> Optional[list]:
        """Get cached survey list."""
        return self.get(f"survey_list:{cache_key}")
    
    def set_survey_list(self, cache_key: str, surveys: list, ttl: int = 60) -> bool:
        """Cache survey list."""
        return self.set(f"survey_list:{cache_key}", surveys, ttl)


cache_service = CacheService()
