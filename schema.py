"""Output schema for the grading step (Session 1, Table 2) and validation.

Two levels of validity, kept separate on purpose:
  - syntactic: Pydantic can parse the JSON into the model (form)
  - semantic : the values agree with each other and with the input (content)
"""
import re
from typing import Literal

from pydantic import BaseModel, Field

ErrorType = Literal["unit", "rearrangement", "arithmetic", "concept", "incomplete", "none"]


class PointJudgement(BaseModel):
    point: str = Field(description="The marking point being judged")
    awarded: bool
    evidence: str = Field(
        description="Words copied EXACTLY from the student answer that earn this point. "
        "Empty string if the point is not awarded."
    )


class ReasonFirst(BaseModel):
    """marking_points come BEFORE total_mark: the model writes its reasons, then the mark."""

    marking_points: list[PointJudgement]
    total_mark: int = Field(description="Number of awarded points; not more than max_mark")
    error_type: ErrorType
    misconception: str = Field(description="The underlying misconception, or empty string")
    feedback: str = Field(description="Short feedback for the student, without giving the full answer")


class MarkFirst(BaseModel):
    """total_mark comes FIRST: the mark is decided before any reason is written."""

    total_mark: int = Field(description="Number of awarded points; not more than max_mark")
    marking_points: list[PointJudgement]
    error_type: ErrorType
    misconception: str = Field(description="The underlying misconception, or empty string")
    feedback: str = Field(description="Short feedback for the student, without giving the full answer")


SCHEMAS = {"reason_first": ReasonFirst, "mark_first": MarkFirst}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def semantic_issues(g, max_mark: int, student_answer: str, n_scheme_points: int | None = None) -> list[str]:
    """Return a sorted list of issue codes. Empty list = semantically valid.

    Assumes each marking point is worth one mark (true for most IGCSE Physics points).
    """
    issues = set()
    awarded = sum(p.awarded for p in g.marking_points)
    if g.total_mark != awarded:
        issues.add("total_not_sum_of_points")
    if not 0 <= g.total_mark <= max_mark:
        issues.add("total_out_of_range")
    answer = _norm(student_answer)
    for p in g.marking_points:
        if p.awarded and not p.evidence.strip():
            issues.add("awarded_without_evidence")
        elif p.awarded and _norm(p.evidence) not in answer:
            issues.add("evidence_not_in_answer")  # the model invented or paraphrased its evidence
    if n_scheme_points is not None and len(g.marking_points) != n_scheme_points:
        issues.add("point_count_mismatch")
    if g.error_type == "none" and g.total_mark < max_mark:
        issues.add("error_none_but_marks_lost")
    return sorted(issues)
