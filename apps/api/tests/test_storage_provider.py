import os
import tempfile
import pytest
from app.services.storage_service import LocalStorageProvider


def test_storage_save_and_read():
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = LocalStorageProvider(base_path=tmpdir)
        content = b"Hello, VisualNote AI Phase 2 storage!"
        key = "notes/test_note.txt"

        stored_key = provider.save(key, content)
        assert stored_key == key
        assert provider.exists(key) is True

        read_content = provider.read(key)
        assert read_content == content


def test_storage_delete():
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = LocalStorageProvider(base_path=tmpdir)
        key = "temp/to_delete.txt"
        provider.save(key, b"delete me")
        assert provider.exists(key) is True

        deleted = provider.delete(key)
        assert deleted is True
        assert provider.exists(key) is False

        # Deleting non-existent file returns False
        assert provider.delete("non_existent.txt") is False


def test_storage_path_traversal_protection():
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = LocalStorageProvider(base_path=tmpdir)

        # Attempt path traversal
        with pytest.raises(ValueError, match="Path traversal detected"):
            provider.save("../evil.txt", b"malicious")

        with pytest.raises(ValueError, match="Path traversal detected"):
            provider.read("../../etc/passwd")

        with pytest.raises(ValueError, match="Path traversal detected"):
            provider.exists("../../../outside.txt")

        with pytest.raises(ValueError, match="Path traversal detected"):
            provider.delete("../escape.txt")
