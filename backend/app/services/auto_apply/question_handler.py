"""Deterministic question handling — safe answers only."""

from __future__ import annotations

from app.models.auto_apply import DetectedQuestion


def build_apply_preferences(
    *,
    notice_period_days: int = 30,
    willing_to_relocate: bool = True,
    work_authorization: str = "Authorized to work",
    expected_salary: str = "",
) -> dict[str, str]:
    return {
        "notice_period": f"{notice_period_days} days",
        "relocation": "Yes" if willing_to_relocate else "No",
        "work_authorization": work_authorization,
        "expected_salary": expected_salary,
    }


def resolve_question(
    label: str,
    field_type: str,
    *,
    profile: dict[str, str],
    preferences: dict[str, str],
) -> DetectedQuestion:
    text = label.lower()
    question_type = field_type

    if field_type == "years_of_experience" or "year" in text and "experience" in text:
        answer = profile.get("years_of_experience", "")
        return DetectedQuestion(
            label=label,
            question_type="years_of_experience",
            suggested_answer=answer,
            confidence=0.8 if answer else 0.0,
            requires_confirmation=not bool(answer),
            answered=bool(answer),
        )

    if field_type == "notice_period" or "notice" in text:
        answer = preferences.get("notice_period", "30 days")
        return DetectedQuestion(
            label=label,
            question_type="notice_period",
            suggested_answer=answer,
            confidence=0.9,
            requires_confirmation=True,
            answered=True,
        )

    if field_type == "relocation" or "relocate" in text:
        answer = preferences.get("relocation", "Yes")
        return DetectedQuestion(
            label=label,
            question_type="relocation",
            suggested_answer=answer,
            confidence=0.85,
            requires_confirmation=True,
            answered=True,
        )

    if field_type in ("work_authorization",) or any(
        k in text for k in ("visa", "sponsor", "authorization", "work permit")
    ):
        answer = preferences.get("work_authorization", "")
        return DetectedQuestion(
            label=label,
            question_type="work_authorization",
            suggested_answer=answer,
            confidence=0.7 if answer else 0.0,
            requires_confirmation=True,
            answered=bool(answer),
        )

    if field_type == "salary" or any(k in text for k in ("salary", "compensation", "ctc")):
        answer = preferences.get("expected_salary", "")
        return DetectedQuestion(
            label=label,
            question_type="expected_salary",
            suggested_answer=answer,
            confidence=0.5 if answer else 0.0,
            requires_confirmation=True,
            answered=bool(answer),
        )

    return DetectedQuestion(
        label=label,
        question_type=question_type or "unknown",
        suggested_answer="",
        confidence=0.0,
        requires_confirmation=True,
        answered=False,
    )


def partition_questions(
    questions: list[DetectedQuestion],
) -> tuple[list[DetectedQuestion], list[str]]:
    known: list[DetectedQuestion] = []
    unknown: list[str] = []
    for q in questions:
        if q.requires_confirmation and not q.answered:
            unknown.append(q.label)
        else:
            known.append(q)
    return known, unknown
