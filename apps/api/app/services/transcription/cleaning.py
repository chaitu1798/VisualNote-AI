import re
import math
from typing import List, Tuple, Dict, Any
from app.schemas.transcript import TranscriptSegment


class TranscriptCleaningError(Exception):
    """Exception raised when transcript content is invalid."""
    pass


class TranscriptCleaner:
    """Service to normalize and clean educational transcripts while preserving facts, formulas, and technical terms."""

    MAX_TRANSCRIPT_LENGTH = 1_000_000  # 1 million characters limit

    @staticmethod
    def clean_text(raw_text: str) -> str:
        """Cleans raw text while strictly preserving formulas, symbols, and technical terms."""
        if not raw_text or not raw_text.strip():
            raise TranscriptCleaningError("Transcript text cannot be empty.")

        if len(raw_text) > TranscriptCleaner.MAX_TRANSCRIPT_LENGTH:
            raise TranscriptCleaningError(
                f"Transcript exceeds maximum allowed length of {TranscriptCleaner.MAX_TRANSCRIPT_LENGTH} characters."
            )

        text = raw_text.strip()

        # Normalize diverse line break patterns to \n
        text = re.sub(r"\r\n|\r", "\n", text)

        # Replace excessive blank lines (more than 2 consecutive) with a single blank line
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Replace multiple horizontal spaces or tabs with a single space (preserve newlines)
        text = re.sub(r"[^\S\n]+", " ", text)

        # Remove obvious identical word stutters (e.g., "we we", "the the") case-insensitively
        # Only for common conversational stopwords to avoid breaking technical terms or formulas
        stopwords = r"\b(the|a|an|in|on|at|of|to|for|is|are|was|were|we|you|they|it|that|this)\s+\1\b"
        text = re.sub(stopwords, r"\1", text, flags=re.IGNORECASE)

        # Strip spaces around newlines
        lines = [line.strip() for line in text.split("\n")]
        cleaned = "\n".join(lines).strip()

        return cleaned

    @staticmethod
    def clean_segments(segments: List[Dict[str, Any]]) -> List[TranscriptSegment]:
        """Validates, cleans, and sorts timed transcript segments safely."""
        if not segments:
            return []

        cleaned_segments: List[TranscriptSegment] = []
        for s in segments:
            if not isinstance(s, dict):
                continue

            text = str(s.get("text", "")).strip()
            if not text:
                continue

            # Safe numeric conversion
            try:
                raw_start = float(s.get("start", 0.0))
                start = 0.0 if (math.isnan(raw_start) or math.isinf(raw_start) or raw_start < 0) else raw_start
            except (ValueError, TypeError):
                start = 0.0

            try:
                raw_end = float(s.get("end", start + 2.0))
                end = (start + 2.0) if (math.isnan(raw_end) or math.isinf(raw_end) or raw_end < start) else raw_end
            except (ValueError, TypeError):
                end = start + 2.0

            text_clean = re.sub(r"[^\S\n]+", " ", text)
            cleaned_segments.append(TranscriptSegment(start=round(start, 2), end=round(end, 2), text=text_clean))

        # Sort strictly by start timestamp
        cleaned_segments.sort(key=lambda seg: seg.start)
        return cleaned_segments

    @classmethod
    def segment_text_if_missing(cls, text: str, estimated_wpm: int = 140) -> List[TranscriptSegment]:
        """
        Creates synthetic timestamped segments for plain text input so the downstream
        pipeline always has timestamped segments.
        """
        cleaned = cls.clean_text(text)
        sentences = re.split(r"(?<=[.?!])\s+", cleaned)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            sentences = [cleaned]

        segments: List[TranscriptSegment] = []
        current_time = 0.0

        for sentence in sentences:
            words = len(sentence.split())
            duration = max(2.0, round((words / estimated_wpm) * 60, 2))
            segments.append(
                TranscriptSegment(
                    start=round(current_time, 2),
                    end=round(current_time + duration, 2),
                    text=sentence,
                )
            )
            current_time += duration

        return segments

    @classmethod
    def process(cls, raw_text: str, segments: List[Dict[str, Any]] = None) -> Tuple[str, List[TranscriptSegment], float]:
        """
        Main processing method. Returns (cleaned_text, cleaned_segments, duration_sec).
        """
        cleaned_text = cls.clean_text(raw_text)

        if segments and len(segments) > 0:
            cleaned_segments = cls.clean_segments(segments)
            duration = cleaned_segments[-1].end if cleaned_segments else 0.0
        else:
            cleaned_segments = cls.segment_text_if_missing(cleaned_text)
            duration = cleaned_segments[-1].end if cleaned_segments else 0.0

        return cleaned_text, cleaned_segments, duration
