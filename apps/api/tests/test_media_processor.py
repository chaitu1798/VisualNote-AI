import pytest
from app.services.media.media_processor import MediaProcessor, MediaProcessingError


def test_media_processor_supported_extensions():
    proc = MediaProcessor(max_size_mb=10)
    for ext in (".mp4", ".mov", ".webm", ".mp3", ".wav", ".m4a"):
        name, mime = proc.validate_file(f"lecture{ext}", 1024)
        assert name == f"lecture{ext}"
        assert mime is not None


def test_media_processor_rejects_unsupported():
    proc = MediaProcessor(max_size_mb=10)
    with pytest.raises(MediaProcessingError) as exc:
        proc.validate_file("malicious.exe", 1024)
    assert exc.value.code == "UNSUPPORTED_MEDIA_TYPE"

    with pytest.raises(MediaProcessingError) as exc2:
        proc.validate_file("document.pdf", 1024)
    assert exc2.value.code == "UNSUPPORTED_MEDIA_TYPE"


def test_media_processor_file_size_limit():
    proc = MediaProcessor(max_size_mb=1)  # 1 MB max
    with pytest.raises(MediaProcessingError) as exc:
        proc.validate_file("large.mp4", 2 * 1024 * 1024)  # 2 MB
    assert exc.value.code == "FILE_TOO_LARGE"


def test_media_processor_sanitization():
    proc = MediaProcessor(max_size_mb=10)
    # Path traversal attempts
    name, _ = proc.validate_file("../../etc/passwd.mp4", 100)
    assert "/" not in name
    assert "\\" not in name
    assert ".." not in name
    assert name.endswith(".mp4")

    name_win, _ = proc.validate_file("..\\..\\test.mp4", 100)
    assert "/" not in name_win
    assert "\\" not in name_win
    assert ".." not in name_win
    assert name_win.endswith(".mp4")

    # Command injection attempts
    name_inj, _ = proc.validate_file("test;whoami.mp4", 100)
    assert ";" not in name_inj
    assert name_inj.endswith(".mp4")

    name_inj2, _ = proc.validate_file("test && whoami.mp4", 100)
    assert "&" not in name_inj2
    assert name_inj2.endswith(".mp4")

    # Empty base name
    name2, _ = proc.validate_file("...mp3", 100)
    assert name2.endswith(".mp3")
    assert len(name2) > 4

