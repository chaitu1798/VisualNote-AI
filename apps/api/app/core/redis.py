import logging
from typing import Optional
import redis
from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """Returns a singleton Redis client instance."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=2.0,
                socket_connect_timeout=2.0,
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Redis client: {e}")
            return None
    return _redis_client


def check_redis_connection() -> bool:
    """Executes a real PING command to verify Redis connectivity."""
    try:
        client = get_redis_client()
        if client is None:
            return False
        return client.ping() is True
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        return False
