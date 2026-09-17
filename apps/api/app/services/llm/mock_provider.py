import uuid
import re
from typing import List, Optional
import logging

from app.schemas.transcript import TranscriptSegment
from app.schemas.concept import (
    Concept,
    ConceptStep,
    ConceptComparison,
    ConceptFormula,
    ConceptAnalysisResponse,
    SourceRange,
)
from app.services.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class MockLLMProvider(LLMProvider):
    """Deterministic Mock LLM Provider covering all 9 concept types for local development, CI, and tracer bullet."""

    async def extract_concepts(
        self,
        transcript_text: str,
        segments: Optional[List[TranscriptSegment]] = None,
        learning_level: str = "INTERMEDIATE"
    ) -> ConceptAnalysisResponse:
        logger.info(f"MockLLMProvider: extracting concepts from transcript ({len(transcript_text)} chars)")
        text_lower = transcript_text.lower()

        # Determine start/end ranges from segments if available
        start_t = segments[0].start if segments else 0.0
        end_t = segments[-1].end if segments else 60.0

        if "operating system" in text_lower or "cpu scheduler" in text_lower or "kernel space" in text_lower:
            return self._os_concepts(start_t, end_t)
        elif "relational database" in text_lower or "sql" in text_lower or "acid" in text_lower:
            return self._db_concepts(start_t, end_t)
        elif "three-way handshake" in text_lower or "tcp" in text_lower or "syn" in text_lower:
            return self._network_concepts(start_t, end_t)
        elif "precision" in text_lower or "recall" in text_lower or "f1" in text_lower:
            return self._ml_concepts(start_t, end_t)
        else:
            return self._generic_concepts(transcript_text, start_t, end_t)

    def _os_concepts(self, start_t: float, end_t: float) -> ConceptAnalysisResponse:
        c1 = Concept(
            id=f"concept-{uuid.uuid4().hex[:6]}",
            title="Operating System",
            concept_type="definition",
            importance_score=0.95,
            source=SourceRange(start=start_t, end=round(start_t + (end_t - start_t) * 0.4, 2)),
            explanation="System software that manages computer hardware and software resources and provides common services for application programs.",
            visual_type="concept_card",
            confidence=0.98,
            supporting_points=[
                "Process management and CPU scheduling",
                "Dynamic memory allocation and virtual memory paging",
                "File system organization and access control",
                "Hardware abstraction and device I/O management",
            ],
            examples=["Linux", "macOS", "Windows", "FreeBSD"],
        )

        c2 = Concept(
            id=f"concept-{uuid.uuid4().hex[:6]}",
            title="CPU Process Scheduling",
            concept_type="process",
            importance_score=0.88,
            source=SourceRange(start=round(start_t + (end_t - start_t) * 0.3, 2), end=round(start_t + (end_t - start_t) * 0.7, 2)),
            explanation="The mechanism by which the operating system decides which runnable process is assigned CPU execution time.",
            visual_type="flowchart",
            confidence=0.92,
            steps=[
                ConceptStep(name="New / Created", description="Process is initially allocated in memory"),
                ConceptStep(name="Ready Queue", description="Process awaits CPU time slice allocation"),
                ConceptStep(name="Running State", description="CPU executes process instructions"),
                ConceptStep(name="Waiting / Terminated", description="Process awaits I/O completion or exits cleanly"),
            ],
            supporting_points=["Preemptive vs non-preemptive algorithms", "Context switching overhead"],
        )

        c3 = Concept(
            id=f"concept-{uuid.uuid4().hex[:6]}",
            title="Virtual Memory & Paging",
            concept_type="relationship",
            importance_score=0.82,
            source=SourceRange(start=round(start_t + (end_t - start_t) * 0.6, 2), end=end_t),
            explanation="Memory management technique that creates an illusion of large contiguous physical memory using disk-backed page tables.",
            visual_type="concept_map",
            confidence=0.90,
            supporting_points=[
                "Translates virtual addresses to physical RAM frames",
                "Enables paging to secondary storage during memory pressure",
                "Protects individual process memory spaces",
            ],
            examples=["4KB Page size", "Translation Lookaside Buffer (TLB)"],
        )

        return ConceptAnalysisResponse(
            title="Introduction to Operating Systems",
            summary="A comprehensive overview of operating system architectures, process scheduling lifecycles, and virtual memory management.",
            concepts=[c1, c2, c3],
        )

    def _db_concepts(self, start_t: float, end_t: float) -> ConceptAnalysisResponse:
        c1 = Concept(
            id=f"concept-{uuid.uuid4().hex[:6]}",
            title="Relational Database Management System",
            concept_type="definition",
            importance_score=0.94,
            source=SourceRange(start=start_t, end=round(start_t + (end_t - start_t) * 0.4, 2)),
            explanation="Data management system that structures information into tables of rows and columns with enforced relationships and constraints.",
            visual_type="concept_card",
            confidence=0.96,
            supporting_points=[
                "Primary keys uniquely identify records",
                "Foreign keys enforce referential integrity across entities",
                "SQL provides declarative schema definition and data manipulation",
            ],
            examples=["PostgreSQL", "MySQL", "SQLite"],
        )

        c2 = Concept(
            id=f"concept-{uuid.uuid4().hex[:6]}",
            title="SQL vs NoSQL Architecture",
            concept_type="comparison",
            importance_score=0.86,
            source=SourceRange(start=round(start_t + (end_t - start_t) * 0.35, 2), end=round(start_t + (end_t - start_t) * 0.75, 2)),
            explanation="Architectural trade-offs between structured relational stores and horizontally scalable document/key-value databases.",
            visual_type="comparison_table",
            confidence=0.91,
            comparison=ConceptComparison(
                entities=["SQL (Relational)", "NoSQL (Distributed)"],
                aspects={
                    "Schema": ["Strict, predefined schema", "Flexible, dynamic schema"],
                    "Scaling": ["Vertical (scale-up hardware)", "Horizontal (scale-out clusters)"],
                    "Transactions": ["Strict ACID compliance", "BASE / Eventual consistency"],
                },
            ),
            supporting_points=["CAP Theorem considerations", "Query complexity vs write throughput"],
        )

        c3 = Concept(
            id=f"concept-{uuid.uuid4().hex[:6]}",
            title="ACID Transaction Guarantees",
            concept_type="list",
            importance_score=0.80,
            source=SourceRange(start=round(start_t + (end_t - start_t) * 0.7, 2), end=end_t),
            explanation="The four primary properties that guarantee database transactions are processed reliably.",
            visual_type="bullet_list",
            confidence=0.93,
            supporting_points=[
                "Atomicity: All operations in the transaction succeed or all fail",
                "Consistency: Database transitions between valid states preserving constraints",
                "Isolation: Concurrent execution yields identical results to sequential execution",
                "Durability: Committed transactions persist permanently across crashes",
            ],
        )

        return ConceptAnalysisResponse(
            title="Relational Databases and SQL",
            summary="Exploration of relational database schemas, referential integrity, and comparison between SQL and NoSQL storage engines.",
            concepts=[c1, c2, c3],
        )

    def _network_concepts(self, start_t: float, end_t: float) -> ConceptAnalysisResponse:
        c1 = Concept(
            id=f"concept-{uuid.uuid4().hex[:6]}",
            title="TCP Three-Way Handshake",
            concept_type="process",
            importance_score=0.95,
            source=SourceRange(start=start_t, end=round(start_t + (end_t - start_t) * 0.6, 2)),
            explanation="Deterministic synchronization protocol used to establish a reliable, full-duplex TCP transport connection.",
            visual_type="flowchart",
            confidence=0.97,
            steps=[
                ConceptStep(name="1. SYN", description="Client sends SYN flag with initial sequence number seq=x"),
                ConceptStep(name="2. SYN-ACK", description="Server replies with SYN-ACK, ack=x+1 and seq=y"),
                ConceptStep(name="3. ACK", description="Client confirms with ACK, ack=y+1, completing connection"),
            ],
            supporting_points=[
                "Guarantees both endpoints can transmit and receive data",
                "Synchronizes starting sequence numbers for reliable byte ordering",
                "Prevents stale duplicate connection requests from corrupting state",
            ],
        )

        c2 = Concept(
            id=f"concept-{uuid.uuid4().hex[:6]}",
            title="Evolution of Transport Protocols",
            concept_type="timeline",
            importance_score=0.78,
            source=SourceRange(start=round(start_t + (end_t - start_t) * 0.5, 2), end=end_t),
            explanation="Historical milestone timeline tracing the development of host-to-host transport protocols.",
            visual_type="timeline",
            confidence=0.88,
            supporting_points=[
                "1974: Transmission Control Program proposed by Vint Cerf and Bob Kahn",
                "1981: TCP RFC 793 published separating TCP from IP",
                "1990s: Fast Retransmit and Congestion Avoidance algorithms introduced",
                "2012+: Multipath TCP and QUIC modern transport innovations",
            ],
        )

        return ConceptAnalysisResponse(
            title="Computer Networks: TCP Handshake",
            summary="Detailed breakdown of the three-way handshake mechanism establishing dependable end-to-end transport sockets.",
            concepts=[c1, c2],
        )

    def _ml_concepts(self, start_t: float, end_t: float) -> ConceptAnalysisResponse:
        c1 = Concept(
            id=f"concept-{uuid.uuid4().hex[:6]}",
            title="Classification Precision & Recall",
            concept_type="formula",
            importance_score=0.96,
            source=SourceRange(start=start_t, end=round(start_t + (end_t - start_t) * 0.6, 2)),
            explanation="Essential evaluation metrics for imbalanced classification tasks balancing false positives and false negatives.",
            visual_type="formula_block",
            confidence=0.95,
            formula=ConceptFormula(
                expression=r"\text{Precision} = \frac{TP}{TP + FP}, \quad \text{Recall} = \frac{TP}{TP + FN}",
                variables={
                    "TP": "True Positives (correctly identified positive cases)",
                    "FP": "False Positives (negative cases incorrectly identified as positive)",
                    "FN": "False Negatives (positive cases missed by the model)",
                },
                explanation="Precision measures exactness; Recall measures completeness.",
            ),
            supporting_points=[
                "Precision is crucial when false alarms are costly (e.g., spam detection)",
                "Recall is critical when missed detections are fatal (e.g., cancer diagnosis)",
            ],
        )

        c2 = Concept(
            id=f"concept-{uuid.uuid4().hex[:6]}",
            title="Spam Filtering Example",
            concept_type="example",
            importance_score=0.76,
            source=SourceRange(start=round(start_t + (end_t - start_t) * 0.5, 2), end=end_t),
            explanation="Concrete industry application of high-precision classification models.",
            visual_type="example_card",
            confidence=0.90,
            supporting_points=[
                "Email classification system where moving legitimate email to spam causes high user friction",
                "Model is tuned for high Precision (> 0.98) even at the cost of lower Recall",
            ],
            examples=["Gmail Spam Filter", "Phishing URL Filter"],
        )

        return ConceptAnalysisResponse(
            title="Machine Learning Evaluation: Precision and Recall",
            summary="Mathematical formulations and trade-offs of Precision, Recall, and the harmonic F1 Score in model evaluation.",
            concepts=[c1, c2],
        )

    def _generic_concepts(self, text: str, start_t: float, end_t: float) -> ConceptAnalysisResponse:
        """Generic heuristic extractor for arbitrary educational text."""
        sentences = [s.strip() for s in re.split(r"[.!?]\s+", text) if s.strip()]
        first_sentence = sentences[0] if sentences else "Key Concept"

        # Determine candidate title from first sentence
        words = first_sentence.split()
        title = " ".join(words[:5]).rstrip(":,-.")
        if len(title) < 3:
            title = "Core Educational Concept"

        c1 = Concept(
            id=f"concept-{uuid.uuid4().hex[:6]}",
            title=title.title(),
            concept_type="general",
            importance_score=0.85,
            source=SourceRange(start=start_t, end=end_t),
            explanation=first_sentence,
            visual_type="concept_card",
            confidence=0.85,
            supporting_points=[s for s in sentences[1:5] if len(s) > 10],
            examples=[],
        )

        return ConceptAnalysisResponse(
            title=title.title(),
            summary=first_sentence,
            concepts=[c1],
        )
