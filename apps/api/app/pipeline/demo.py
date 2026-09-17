import asyncio
import sys
from app.fixtures.sample_transcripts import SAMPLE_TRANSCRIPTS
from app.schemas.generation import PipelineRunRequest
from app.services.pipeline_service import get_pipeline_service


async def run_demo(topic_key: str = "operating_systems"):
    fixture = SAMPLE_TRANSCRIPTS.get(topic_key, SAMPLE_TRANSCRIPTS["operating_systems"])
    title = fixture["title"]
    text = fixture["text"]

    print("=" * 70)
    print("  VISUALNOTE AI — PHASE 1 TRACER BULLET DEMO")
    print("=" * 70)
    print(f"Source Topic:       {fixture.get('topic', 'Computer Science')}")
    print(f"Source Title:       {title}")
    print(f"Transcript Length:  {len(text)} characters ({len(text.split())} words)")
    print(f"Input Preview:      {text[:120]}...\n")

    print(">>> Executing Core AI Pipeline (Mock Mode: Deterministic)...")
    pipeline = get_pipeline_service()
    req = PipelineRunRequest(
        raw_text=text,
        theme="clean_handwritten",
        learning_level="INTERMEDIATE",
        mock_mode=True,
    )

    result = await pipeline.run_pipeline(request=req)

    print("\n" + "-" * 70)
    print(f"Processing Status:  {result.status} (Stage: {result.current_stage}, Progress: {result.progress*100:.0f}%)")
    print(f"Transcript Segments: {len(result.transcript.segments) if result.transcript else 0}")
    print(f"Concept Count:      {len(result.concepts) if result.concepts else 0}")

    if result.concepts:
        print("\nExtracted Concepts (Ranked by Deterministic Importance):")
        for i, c in enumerate(result.concepts, 1):
            print(f"  {i}. [{c.concept_type.upper()}] {c.title} (Importance: {c.importance_score:.2f}, Template: {c.visual_type})")

    if result.visual_plan:
        print(f"\nVisual Plan Sections: {len(result.visual_plan.sections)}")
        for sec in result.visual_plan.sections:
            print(f"  • Priority {sec.priority}: {sec.title} -> Layout: {sec.visual_type} ({sec.theme})")

    if result.render_result:
        print("\nRendered Artifacts:")
        print(f"  HTML Note:    {result.render_result.html_url}")
        if result.render_result.image_url:
            print(f"  PNG Visual:   {result.render_result.image_url}")
        print(f"  Storage Path: {result.render_result.storage_path}")

    print("=" * 70)
    print("  TRACER BULLET DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    return result


def main():
    topic = sys.argv[1] if len(sys.argv) > 1 else "operating_systems"
    asyncio.run(run_demo(topic))


if __name__ == "__main__":
    main()
