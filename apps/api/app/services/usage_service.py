from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class UsageService:
    """Service tracking resource usage and quota enforcement."""

    def __init__(self):
        # In Phase 0, usage counters are structured for future persistence
        self._in_memory_counters: Dict[str, Dict[str, int]] = {}

    def get_user_usage(self, user_id: str) -> Dict[str, Any]:
        """Returns the current usage counters for a user."""
        return self._in_memory_counters.get(
            user_id,
            {
                "videos_processed": 0,
                "pages_generated": 0,
                "pages_regenerated": 0,
                "exports_created": 0,
                "credits_used": 0,
            },
        )

    def check_allowed(self, user_id: str, action: str, amount: int = 1) -> bool:
        """Verifies if the requested action is within quota."""
        # In Phase 0 (development/FYP), standard operations are allowed by default
        return True

    def record(self, user_id: str, action: str, amount: int = 1) -> None:
        """Records an action against the user's usage."""
        if user_id not in self._in_memory_counters:
            self._in_memory_counters[user_id] = {
                "videos_processed": 0,
                "pages_generated": 0,
                "pages_regenerated": 0,
                "exports_created": 0,
                "credits_used": 0,
            }
        current = self._in_memory_counters[user_id].get(action, 0)
        self._in_memory_counters[user_id][action] = current + amount
        logger.info(f"Usage recorded: user={user_id}, action={action}, +{amount}")


_usage_service: Optional[UsageService] = None


def get_usage_service() -> UsageService:
    global _usage_service
    if _usage_service is None:
        _usage_service = UsageService()
    return _usage_service
