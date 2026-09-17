import pytest
from app.services.transcription.cleaning import TranscriptCleaner, TranscriptCleaningError
from app.services.transcription.mock_provider import MockTranscriptionProvider


def test_transcript_cleaner_whitespace_and_stutters():
    raw = "An  operating   system  is  the the  core  software.\n\n\n\nIt manages   memory."
    cleaned = TranscriptCleaner.clean_text(raw)
    assert "An operating system is the core software." in cleaned
    assert "It manages memory." in cleaned
    assert "the the" not in cleaned


def test_transcript_cleaner_empty():
    with pytest.raises(TranscriptCleaningError):
        TranscriptCleaner.clean_text("")

    with pytest.raises(TranscriptCleaningError):
        TranscriptCleaner.clean_text("   \n\t  ")


def test_transcript_cleaner_preserves_formulas():
    formula_text = "The metric formula is: Precision = TP / (TP + FP)."
    cleaned = TranscriptCleaner.clean_text(formula_text)
    assert "Precision = TP / (TP + FP)" in cleaned


def test_transcript_cleaner_preserves_technical_terms_and_symbols():
    tech_text = "CPU and RAM communicate over TCP/IP and HTTP with SQL database. Complexity is O(n). Energy is E = mc², x², sum is Σ, arrow →, range ≤ and ≥."
    cleaned = TranscriptCleaner.clean_text(tech_text)
    for term in ["CPU", "RAM", "TCP/IP", "HTTP", "SQL", "O(n)", "E = mc²", "x²", "Σ", "→", "≤", "≥"]:
        assert term in cleaned



def test_segment_text_if_missing():
    text = "First concept sentence. Second concept sentence with more detail."
    segments = TranscriptCleaner.segment_text_if_missing(text)
    assert len(segments) == 2
    assert segments[0].start == 0.0
    assert segments[0].end > 0.0
    assert segments[1].start == segments[0].end
    assert segments[1].end > segments[1].start


@pytest.mark.asyncio
async def test_mock_transcription_provider():
    provider = MockTranscriptionProvider()
    res = await provider.transcribe_text("Operating system manages hardware.")
    assert len(res.text) > 0
    assert len(res.segments) > 0
    assert res.provider == "mock"
    assert res.duration > 0.0
