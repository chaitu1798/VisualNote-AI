from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path
import os
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageProvider(ABC):
    """Abstract base class / interface for storage providers."""

    @abstractmethod
    def save(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Persists data with the given key and returns the storage path/key."""
        pass

    @abstractmethod
    def read(self, key: str) -> Optional[bytes]:
        """Retrieves raw data for a given key, or None if not found."""
        pass

    def get(self, key: str) -> Optional[bytes]:
        """Backward compatibility alias for read()."""
        return self.read(key)

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


# Backward compatibility alias
StorageService = StorageProvider


class LocalStorageProvider(StorageProvider):
    """Local filesystem storage implementation for development."""

    def __init__(self, base_dir: Optional[str] = None, base_path: Optional[str] = None):
        target = base_dir or base_path or settings.STORAGE_LOCAL_DIR
        self.base_dir = Path(target).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, key: str) -> Path:
        norm_key = key.replace("\\", "/").strip()
        parts = norm_key.split("/")
        if ".." in parts or norm_key.startswith("/"):
            raise ValueError(f"Path traversal detected for storage key: {key}")
        resolved = (self.base_dir / key).resolve()
        try:
            resolved.relative_to(self.base_dir)
        except ValueError:
            raise ValueError(f"Path traversal detected for storage key: {key}")
        return resolved

    def save(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        file_path = self._resolve_path(key)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)
        logger.info(f"Saved {len(data)} bytes to {file_path}")
        return key

    def read(self, key: str) -> Optional[bytes]:
        file_path = self._resolve_path(key)
        if not file_path.exists() or not file_path.is_file():
            return None
        return file_path.read_bytes()

    def delete(self, key: str) -> bool:
        file_path = self._resolve_path(key)
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            return True
        return False

    def exists(self, key: str) -> bool:
        file_path = self._resolve_path(key)
        return file_path.exists() and file_path.is_file()


    def get_url(self, key: str) -> str:
        clean_key = key.replace("\\", "/").lstrip("/")
        return f"/storage/{clean_key}"


# Backward compatibility alias
LocalStorageService = LocalStorageProvider

_storage_provider: Optional[StorageProvider] = None


def get_storage_provider() -> StorageProvider:
    global _storage_provider
    if _storage_provider is None:
        if settings.STORAGE_PROVIDER == "local":
            _storage_provider = LocalStorageProvider()
        else:
            _storage_provider = LocalStorageProvider()
    return _storage_provider


# Backward compatibility alias
def get_storage_service() -> StorageProvider:
    return get_storage_provider()

