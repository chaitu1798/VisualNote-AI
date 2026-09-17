import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".webm": "video/webm",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
}

SUPPORTED_MIME_PREFIXES = ("video/", "audio/")


class MediaProcessingError(Exception):
    """Custom error for media validation or processing issues."""
    def __init__(self, message: str, code: str = "MEDIA_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code


class MediaProcessor:
    """Service for validating media files and extracting audio safely."""

    def __init__(self, max_size_mb: Optional[int] = None):
        self.max_size_bytes = (max_size_mb or settings.MAX_UPLOAD_SIZE_MB) * 1024 * 1024

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitizes user filename strictly to prevent path traversal and shell injection.
        Removes all slashes, '..', and dangerous shell metacharacters.
        """
        if not filename:
            return f"upload_{uuid.uuid4().hex[:8]}.mp4"

        # Normalize slashes and take basename
        normalized = filename.replace("\\", "/").strip()
        base_name = os.path.basename(normalized)

        # Remove path traversal sequences and spaces
        base_name = base_name.replace("..", "").strip()

        # Check if there is an extension among supported ones or last dot
        dot_idx = base_name.rfind(".")
        if dot_idx != -1 and dot_idx < len(base_name) - 1:
            raw_stem = base_name[:dot_idx]
            raw_ext = base_name[dot_idx:]
            stem = "".join(c for c in raw_stem if c.isalnum() or c in ("_", "-")).strip("._-")
            ext = "." + "".join(c for c in raw_ext if c.isalnum()).lower()
        else:
            stem = "".join(c for c in base_name if c.isalnum() or c in ("_", "-")).strip("._-")
            ext = ".mp4"

        if not stem:
            stem = f"upload_{uuid.uuid4().hex[:8]}"

        return f"{stem}{ext}"

    def validate_file(self, filename: str, file_size: int, content_type: Optional[str] = None) -> Tuple[str, str]:
        """
        Validates file extension, size, and MIME type.
        Returns (sanitized_filename, mime_type).
        """
        sanitized = self.sanitize_filename(filename)
        ext = Path(sanitized).suffix.lower()

        if ext not in SUPPORTED_EXTENSIONS:
            allowed = ", ".join(sorted(SUPPORTED_EXTENSIONS.keys()))
            raise MediaProcessingError(
                f"Unsupported file format '{ext}'. Supported formats: {allowed}",
                code="UNSUPPORTED_MEDIA_TYPE"
            )

        if file_size > self.max_size_bytes:
            max_mb = self.max_size_bytes / (1024 * 1024)
            raise MediaProcessingError(
                f"File size exceeds maximum allowed limit of {max_mb:.0f} MB.",
                code="FILE_TOO_LARGE"
            )

        expected_mime = SUPPORTED_EXTENSIONS[ext]
        resolved_mime = content_type or expected_mime

        # Soft validation on MIME prefix
        if not any(resolved_mime.startswith(prefix) for prefix in SUPPORTED_MIME_PREFIXES):
            resolved_mime = expected_mime

        return sanitized, resolved_mime

    def check_ffmpeg_available(self) -> bool:
        """Checks if ffmpeg binary is available in PATH."""
        return shutil.which("ffmpeg") is not None

    def extract_audio(self, input_bytes: bytes, filename: str) -> Tuple[bytes, Dict[str, Any]]:
        """
        Extracts or normalizes audio track using FFmpeg if available,
        or returns raw bytes with metadata if input is already audio or FFmpeg is absent.
        Guarantees that raw user filenames are never passed directly to shells.
        """
        sanitized, mime_type = self.validate_file(filename, len(input_bytes))
        is_video = mime_type.startswith("video/")

        if not self.check_ffmpeg_available():
            if is_video:
                raise MediaProcessingError(
                    "FFmpeg is not installed on this system. Cannot extract audio from video. "
                    "Please upload an audio file (.mp3, .wav, .m4a) or provide a transcript.",
                    code="FFMPEG_MISSING"
                )
            logger.info("FFmpeg not found; using raw audio bytes directly.")
            return input_bytes, {
                "format": Path(sanitized).suffix.lstrip("."),
                "extracted_audio": False,
                "duration_sec": 0.0,
            }

        # If ffmpeg is available, extract/normalize audio safely in a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_input = Path(temp_dir) / sanitized
            temp_output = Path(temp_dir) / f"extracted_{uuid.uuid4().hex[:8]}.wav"

            temp_input.write_bytes(input_bytes)

            # Subprocess argument array strictly without shell=True to prevent command injection
            cmd = [
                "ffmpeg",
                "-y",
                "-i", str(temp_input),
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                str(temp_output),
            ]

            try:
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=60,
                    check=False
                )
                if result.returncode != 0 or not temp_output.exists():
                    stderr_msg = result.stderr.decode("utf-8", errors="ignore")
                    logger.warning(f"FFmpeg extraction failed: {stderr_msg[:200]}")
                    if is_video:
                        raise MediaProcessingError(
                            "Failed to process media with FFmpeg. The file may be corrupt.",
                            code="FFMPEG_ERROR"
                        )
                    return input_bytes, {"format": Path(sanitized).suffix.lstrip("."), "extracted_audio": False}

                audio_bytes = temp_output.read_bytes()
                return audio_bytes, {
                    "format": "wav",
                    "extracted_audio": True,
                    "sample_rate": 16000,
                }
            except subprocess.TimeoutExpired:
                raise MediaProcessingError(
                    "Media processing timed out.",
                    code="PROCESSING_TIMEOUT"
                )
            except Exception as exc:
                if isinstance(exc, MediaProcessingError):
                    raise
                logger.error(f"Error during audio extraction: {exc}")
                raise MediaProcessingError(
                    "Unexpected error during media processing.",
                    code="MEDIA_ERROR"
                )


_media_processor: Optional[MediaProcessor] = None


def get_media_processor() -> MediaProcessor:
    global _media_processor
    if _media_processor is None:
        _media_processor = MediaProcessor()
    return _media_processor
