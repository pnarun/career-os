from app.services.job_sources.base.base_source import BaseJobSource
from app.services.job_sources.base.source_result import (
    AggregatorFetchResult,
    NormalizedSourceJob,
    RawSourceJob,
    SourceFetchResult,
)

__all__ = [
    "AggregatorFetchResult",
    "BaseJobSource",
    "NormalizedSourceJob",
    "RawSourceJob",
    "SourceFetchResult",
]
