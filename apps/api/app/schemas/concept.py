from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field, model_validator


class SourceRange(BaseModel):
    start: float = Field(..., ge=0.0, description="Start timestamp in seconds")
    end: float = Field(..., ge=0.0, description="End timestamp in seconds")

    @model_validator(mode="after")
    def validate_range(self) -> "SourceRange":
        if self.end < self.start:
            raise ValueError("source.end cannot be less than source.start")
        return self


class ConceptStep(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = Field(...)


class ConceptComparison(BaseModel):
    entities: List[str] = Field(..., min_length=2)
    aspects: Dict[str, List[str]] = Field(default_factory=dict)


class ConceptFormula(BaseModel):
    expression: str = Field(..., min_length=1, description="Mathematical LaTeX expression")
    variables: Dict[str, str] = Field(default_factory=dict, description="Variable explanations")
    explanation: str = Field(...)


ConceptTypeEnum = Literal[
    "definition",
    "process",
    "comparison",
    "formula",
    "timeline",
    "relationship",
    "example",
    "list",
    "general",
]

VisualTypeEnum = Literal[
    "concept_card",
    "flowchart",
    "comparison_table",
    "formula_block",
    "timeline",
    "concept_map",
    "bullet_list",
    "example_card",
]


class Concept(BaseModel):
    """Canonical Concept JSON schema matching PRD & PWD."""
    id: Optional[str] = Field(default=None, description="Unique identifier for the concept")
    title: str = Field(..., min_length=1, max_length=255)
    concept_type: ConceptTypeEnum = Field(..., description="definition, process, comparison, formula, etc.")
    importance_score: float = Field(..., ge=0.0, le=1.0, description="Importance score between 0.0 and 1.0")
    source: SourceRange
    explanation: str = Field(..., min_length=1)
    visual_type: VisualTypeEnum = Field(..., description="One of the deterministic templates")
    confidence: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    steps: Optional[List[ConceptStep]] = None
    comparison: Optional[ConceptComparison] = None
    formula: Optional[ConceptFormula] = None
    supporting_points: List[str] = Field(default_factory=list)
    examples: List[str] = Field(default_factory=list)


class ConceptAnalysisResponse(BaseModel):
    title: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    concepts: List[Concept] = Field(default_factory=list)


class VisualPlanSchema(BaseModel):
    """Visual Plan specification for layout rendering."""
    visual_type: VisualTypeEnum
    layout: str = Field("default", description="Template layout variation")
    content: Concept
    style: str = Field("handwritten", description="Visual styling preset")
