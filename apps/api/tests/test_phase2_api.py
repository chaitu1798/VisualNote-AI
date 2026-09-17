import uuid
from fastapi.testclient import TestClient


def test_sources_crud_and_transcript(client: TestClient):
    # 1. Ingest text source
    text_payload = {
        "text": "Cellular respiration converts biochemical energy from nutrients into ATP.",
        "title": "Cellular Respiration Notes",
    }
    create_resp = client.post("/api/v1/sources/text", json=text_payload)
    assert create_resp.status_code == 200
    source_data = create_resp.json()
    source_id = source_data["id"]
    assert source_data["title"] == "Cellular Respiration Notes"
    assert source_data["type"] == "text"
    assert source_data["character_count"] == len(text_payload["text"])

    # 2. Get source by ID
    get_resp = client.get(f"/api/v1/sources/{source_id}")
    assert get_resp.status_code == 200
    detail = get_resp.json()
    assert detail["id"] == source_id
    assert detail["title"] == "Cellular Respiration Notes"
    assert detail["has_transcript"] is True

    # 3. Get source transcript
    transcript_resp = client.get(f"/api/v1/sources/{source_id}/transcript")
    assert transcript_resp.status_code == 200
    transcript_data = transcript_resp.json()
    assert transcript_data["source_id"] == source_id
    assert transcript_data["content"] == text_payload["text"]


def test_sources_youtube_metadata_reference(client: TestClient):
    payload = {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "title": "Quantum Physics Lecture",
    }
    resp = client.post("/api/v1/sources/youtube", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "youtube" in data["type"]
    assert data["title"] == "Quantum Physics Lecture"
    assert data["meta_data"]["video_id"] == "dQw4w9WgXcQ"


def test_async_generation_job_creation_and_idempotency(client: TestClient):
    # Create a source first
    source_resp = client.post(
        "/api/v1/sources/text",
        json={"text": "Mitochondria are membrane-bound cell organelles that generate most of the chemical energy.", "title": "Mitochondria"},
    )
    source_id = source_resp.json()["id"]

    idempotency_key = f"client-req-{uuid.uuid4().hex}"
    job_payload = {
        "source_id": source_id,
        "theme": "blueprint",
        "learning_level": "INTERMEDIATE",
    }

    # 1. First submission
    resp1 = client.post(
        "/api/v1/generation",
        json=job_payload,
        headers={"Idempotency-Key": idempotency_key},
    )
    assert resp1.status_code in (200, 201)
    data1 = resp1.json()
    job_id = data1["id"]
    assert data1["status"] in ("QUEUED", "PROCESSING")
    assert data1["current_stage"] == "queued"

    # 2. Second submission with the exact same Idempotency-Key
    resp2 = client.post(
        "/api/v1/generation",
        json=job_payload,
        headers={"Idempotency-Key": idempotency_key},
    )
    assert resp2.status_code in (200, 201)
    data2 = resp2.json()
    # Must return the SAME job_id without creating a new duplicate job
    assert data2["id"] == job_id

    # 3. Query job status
    status_resp = client.get(f"/api/v1/generation/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["id"] == job_id
    assert status_data["source_id"] == source_id
