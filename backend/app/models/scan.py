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
