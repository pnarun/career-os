from pydantic import BaseModel, Field


class RunScanNowRequest(BaseModel):
    preferences_id: str


class RunScanNowResponse(BaseModel):
    status: str
    scan_id: str = ""
    jobs_found: int = 0
    email_sent: bool = False
    email_to: str = ""
    scan_timestamp: str = ""
    stored: int = 0
    email_error: str = ""
    task_id: str = ""


class ScanTaskStatusResponse(BaseModel):
    task_id: str
    scan_id: str = ""
    kind: str
    status: str
    user_id: str = ""
    preference_id: str = ""
    worker_id: str = ""
    error_summary: str = ""
    result_summary: dict = Field(default_factory=dict)
    created_at: str = ""
    claimed_at: str = ""
    started_at: str = ""
    completed_at: str = ""
    dispatch_latency_ms: float | None = None


class EmailPreviewResponse(BaseModel):
    preview_html: str
    jobs_count: int = 0
    scan_id: str = ""
    scan_timestamp: str = ""


class SendEmailNowRequest(BaseModel):
    preferences_id: str


class SendEmailNowResponse(BaseModel):
    status: str
    email_sent: bool
    jobs_sent: int
    email_to: str
    email_type: str = ""
    sent_at: str = ""
    error: str = ""
