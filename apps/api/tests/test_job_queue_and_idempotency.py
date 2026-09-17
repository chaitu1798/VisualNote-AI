import pytest
from app.core.queue import JobQueueService, QueueConnectionError


def test_job_queue_in_memory_fallback():
    # Instantiate service with in-memory fallback enabled
    queue = JobQueueService(allow_test_fallback=True)
    # Force in-memory mode for pure unit testing without requiring active network
    queue._client = None
    queue._explicit_client = True

    # Test enqueue and dequeue
    job_id = "test-job-uuid-123"
    queue.enqueue_job(job_id)
    assert queue.get_queue_length() == 1

    dequeued = queue.dequeue_job(timeout=1)
    assert dequeued is not None
    assert dequeued["job_id"] == job_id
    assert queue.get_queue_length() == 0


def test_job_state_caching():
    queue = JobQueueService(allow_test_fallback=True)
    queue._client = None
    queue._explicit_client = True

    job_id = "test-job-uuid-456"
    state = {
        "status": "analyzing",
        "current_stage": "analyzing",
        "progress_percentage": 50,
        "error_message": None,
    }
    queue.set_job_state(job_id, state)

    cached = queue.get_job_state(job_id)
    assert cached is not None
    assert cached["status"] == "analyzing"
    assert cached["progress_percentage"] == 50


def test_idempotency_key_deduplication():
    queue = JobQueueService(allow_test_fallback=True)
    queue._client = None
    queue._explicit_client = True

    key = "user-client-request-nonce-789"
    job_id = "job-uuid-first-call"

    # First attempt should acquire the idempotency lock (returns None indicating new reservation)
    existing_id = queue.check_or_set_idempotency(key, job_id, ttl=60)
    assert existing_id is None

    # Second attempt with same key returns the existing job ID
    existing_id_2 = queue.check_or_set_idempotency(key, "different-job-id", ttl=60)
    assert existing_id_2 == job_id


def test_queue_connection_error_without_fallback():
    # When allow_test_fallback is False and Redis fails to connect, QueueConnectionError is raised
    queue = JobQueueService(redis_url="redis://invalid-host-that-does-not-exist:9999", allow_test_fallback=False)
    with pytest.raises(QueueConnectionError):
        queue.enqueue_job("some-job-id")
