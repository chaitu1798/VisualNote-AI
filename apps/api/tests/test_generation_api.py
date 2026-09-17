import io
import pytest


def test_sources_text_endpoint(client):
    response = client.post("/api/v1/sources/", data={"source_type": "text", "raw_text": "Sample text."})
    assert response.status_code == 201
    data = response.json()
    assert data["source_type"] == "text"
    assert data["character_count"] == len("Sample text.")


def test_sources_file_upload_validation(client):
    # Unsupported extension
    files = {"file": ("test.exe", io.BytesIO(b"binary data"), "application/x-msdownload")}
    response = client.post("/api/v1/sources/", files=files)
    assert response.status_code == 400

    # Supported extension (.mp3)
    files_valid = {"file": ("lecture.mp3", io.BytesIO(b"ID3mockaudiobytes"), "audio/mpeg")}
    response_valid = client.post("/api/v1/sources/", files=files_valid)
    assert response_valid.status_code == 201
    assert response_valid.json()["mime_type"] == "audio/mpeg"


def test_transcripts_clean_endpoint(client):
    payload = {"content": "An  operating   system  manages memory."}
    response = client.post("/api/v1/transcripts/clean", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["cleaned_text"] == "An operating system manages memory."
    assert len(data["segments"]) > 0


def test_generation_analyze_endpoint(client):
    payload = {"text": "An Operating System is system software that manages hardware."}
    response = client.post("/api/v1/generation/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "title" in data
    assert len(data["concepts"]) >= 1


def test_generation_pipeline_endpoint(client):
    payload = {
        "raw_text": "An Operating System is system software that manages hardware resources.",
        "theme": "clean_handwritten",
    }
    response = client.post("/api/v1/generation/pipeline", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["current_stage"] == "completed"
    assert data["job_id"] is not None
    assert data["render_result"] is not None

    # Retrieve job status
    job_id = data["job_id"]
    status_resp = client.get(f"/api/v1/generation/{job_id}")
    assert status_resp.status_code == 200
    job_data = status_resp.json()
    assert job_data["id"] == job_id
    assert job_data["status"] == "COMPLETED"
    assert job_data["progress"] == 1.0


def test_generation_job_not_found(client):
    response = client.get("/api/v1/generation/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404

