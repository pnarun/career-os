"""Resume AI — ATS scoring, optimization, and job-specific tailoring."""

from app.services.resume_ai.ats_scoring_service import compute_ats_score
from app.services.resume_ai.jd_resume_alignment import align_resume_to_job
from app.services.resume_ai.resume_feedback_service import generate_resume_feedback
from app.services.resume_ai.resume_optimizer import optimize_resume_for_job
from app.services.resume_ai.resume_variant_service import generate_resume_variants
from app.services.resume_ai.skill_gap_service import analyze_skill_gaps
from app.services.resume_ai.keyword_optimizer import analyze_keywords

__all__ = [
    "compute_ats_score",
    "align_resume_to_job",
    "generate_resume_feedback",
    "optimize_resume_for_job",
    "generate_resume_variants",
    "analyze_skill_gaps",
    "analyze_keywords",
]
