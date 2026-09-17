import json
import logging
from typing import Optional, Dict, Any
import redis
from app.core.config import settings
from app.core.redis import get_redis_client

logger = logging.getLogger(__name__)

JOB_QUEUE_KEY = "visualnote:jobs:queue"
JOB_STATE_PREFIX = "visualnote:jobs:state:"
IDEMPOTENCY_PREFIX = "visualnote:idempotency:"


class QueueConnectionError(Exception):
    """Raised when Redis queue operations cannot be completed due to connection loss."""
    pass


class JobQueueService:
    """
    Redis-backed Queue & Idempotency Service:
    - Enqueue job messages to Redis list (LPUSH)
    - Dequeue job messages with blocking timeout (BRPOP)
    - Fast job state caching with TTL
    - Atomic Idempotency checking & reservation (SETNX)
    """

    def __init__(
        self,
        client: Optional[redis.Redis] = None,
        allow_test_fallback: bool = False,
        redis_url: Optional[str] = None,
    ):
        self._allow_test_fallback = allow_test_fallback
        if redis_url:
            self._client = redis.from_url(redis_url, socket_connect_timeout=0.2, socket_timeout=0.2)
            self._explicit_client = True
        elif client is not None:
            self._client = client
            self._explicit_client = True
        else:
            self._client = None
            self._explicit_client = False

        # In-memory queues strictly for isolated tests when explicitly enabled
        self._test_queue = []
        self._test_states = {}
        self._test_idempotency = {}

    @property
    def client(self) -> Optional[redis.Redis]:
        if self._explicit_client:
            return self._client
        return get_redis_client()

    def get_queue_length(self) -> int:
        """Returns the number of jobs waiting in the queue."""
        r = self.client
        if r is not None:
            try:
                return r.llen(JOB_QUEUE_KEY)
            except Exception as e:
                if self._allow_test_fallback:
                    return len(self._test_queue)
                raise QueueConnectionError(f"Redis queue unavailable: {e}")
        elif self._allow_test_fallback:
            return len(self._test_queue)
        raise QueueConnectionError("Redis client is not available.")

    def enqueue_job(self, job_id: str, payload: Optional[Dict[str, Any]] = None) -> bool:
        """Pushes a job to the Redis queue."""
        data = {
            "job_id": job_id,
            "payload": payload or {},
        }
        serialized = json.dumps(data)
        r = self.client
        if r is not None:
            try:
                r.lpush(JOB_QUEUE_KEY, serialized)
                logger.info(f"Enqueued job {job_id} to Redis queue '{JOB_QUEUE_KEY}'")
                return True
            except Exception as e:
                logger.error(f"Failed to enqueue job {job_id} to Redis: {e}")
                raise QueueConnectionError(f"Redis queue unavailable: {e}")
        elif self._allow_test_fallback:
            self._test_queue.insert(0, serialized)
            return True
        else:
            raise QueueConnectionError("Redis client is not available. Queue operation rejected.")

    def dequeue_job(self, timeout: int = 2) -> Optional[Dict[str, Any]]:
        """Pops a job from the Redis queue with blocking timeout."""
        r = self.client
        if r is not None:
            try:
                item = r.brpop(JOB_QUEUE_KEY, timeout=timeout)
                if item:
                    # item is a tuple: (queue_name, data)
                    raw_data = item[1]
                    return json.loads(raw_data)
                return None
            except Exception as e:
                logger.error(f"Failed to dequeue from Redis: {e}")
                raise QueueConnectionError(f"Redis queue unavailable: {e}")
        elif self._allow_test_fallback:
            if self._test_queue:
                return json.loads(self._test_queue.pop())
            return None
        else:
            raise QueueConnectionError("Redis client is not available. Queue operation rejected.")

    def set_job_state(self, job_id: str, state: Dict[str, Any], ttl: int = 3600) -> None:
        """Caches active job state in Redis with expiration."""
        r = self.client
        if r is not None:
            try:
                key = f"{JOB_STATE_PREFIX}{job_id}"
                r.setex(key, ttl, json.dumps(state))
            except Exception as e:
                logger.warning(f"Failed to cache job state in Redis for {job_id}: {e}")
        elif self._allow_test_fallback:
            self._test_states[job_id] = state

    def get_job_state(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves cached job state from Redis."""
        r = self.client
        if r is not None:
            try:
                key = f"{JOB_STATE_PREFIX}{job_id}"
                data = r.get(key)
                if data:
                    return json.loads(data)
                return None
            except Exception as e:
                logger.warning(f"Failed to read job state from Redis for {job_id}: {e}")
                return None
        elif self._allow_test_fallback:
            return self._test_states.get(job_id)
        return None

    def check_or_set_idempotency(self, idempotency_key: str, job_id: str, ttl: int = 86400) -> Optional[str]:
        """
        Atomically checks and registers an idempotency key.
        Returns the existing job_id if the key was already registered,
        or None if successfully registered as new.
        """
        if not idempotency_key:
            return None

        clean_key = f"{IDEMPOTENCY_PREFIX}{idempotency_key}"
        r = self.client
        if r is not None:
            try:
                # set nx: only set if does not exist
                acquired = r.set(clean_key, job_id, nx=True, ex=ttl)
                if acquired:
                    return None  # Successfully reserved key for this job
                # Key already exists: return the previously registered job_id
                existing = r.get(clean_key)
                return str(existing) if existing else None
            except Exception as e:
                logger.error(f"Redis error during idempotency check: {e}")
                raise QueueConnectionError(f"Idempotency store error: {e}")
        elif self._allow_test_fallback:
            if idempotency_key in self._test_idempotency:
                return self._test_idempotency[idempotency_key]
            self._test_idempotency[idempotency_key] = job_id
            return None
        else:
            raise QueueConnectionError("Redis client is not available. Idempotency check rejected.")


_job_queue_service: Optional[JobQueueService] = None


def get_job_queue_service() -> JobQueueService:
    global _job_queue_service
    if _job_queue_service is None:
        _job_queue_service = JobQueueService()
    return _job_queue_service
