from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path
import os
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService(ABC):
    """Abstract base class for storage providers."""

    @abstractmethod
    def save(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Persists data with the given key and returns the storage path/key."""
        pass

    @abstractmethod
    def get(self, key: str) -> Optional[bytes]:
        """Retrieves raw data for a given key, or None if not found."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Deletes object at key, returns True if deleted."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Checks if key exists in storage."""
        pass

    @abstractmethod
    def get_url(self, key: str) -> str:
        """Returns access URL or path for the given key."""
        pass


class LocalStorageService(StorageService):
    """Local filesystem storage implementation for development."""

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or settings.STORAGE_LOCAL_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, key: str) -> Path:
        # Sanitize key to prevent path traversal
        clean_key = key.lstrip("/\\")
        return self.base_dir / clean_key

    def save(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        file_path = self._resolve_path(key)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)
        logger.info(f"Saved {len(data)} bytes to {file_path}")
        return str(file_path.as_posix())

    def get(self, key: str) -> Optional[bytes]:
        file_path = self._resolve_path(key)
        if not file_path.exists():
            return None
        return file_path.read_bytes()

    def delete(self, key: str) -> bool:
        file_path = self._resolve_path(key)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def exists(self, key: str) -> bool:
        return self._resolve_path(key).exists()

    def get_url(self, key: str) -> str:
        file_path = self._resolve_path(key)
        return f"/storage/{key.lstrip('/')}"


_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    global _storage_service
    if _storage_service is None:
        if settings.STORAGE_PROVIDER == "local":
            _storage_service = LocalStorageService()
        else:
            # Fallback to local for dev
            _storage_service = LocalStorageService()
    return _storage_service
