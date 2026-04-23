from typing import Optional
from pydantic import BaseModel, Field


class MessageAnalyzeDTO(BaseModel):
    session_key: str
    content: str
    detectors: Optional[list[str]] = None
    model: Optional[str] = None


class MessageAnalyzeResponseDTO(BaseModel):
    session_key: str
    assistant_response: str
    incident_detected: bool
    input_detected: bool
    output_detected: bool
    detectors_used: list[str] = Field(default_factory=list)
    incident_id: Optional[int] = None
    incident_code: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
