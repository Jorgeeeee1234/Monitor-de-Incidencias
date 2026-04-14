from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.domain.enums import IncidentStatus


class IncidentResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_code: str
    session_id: int
    category: str
    severity: str
    priority: str
    status: IncidentStatus
    confidence: float
    detection_method: str
    input_text: str
    output_text: Optional[str]
    notes: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]


class IncidentStatusUpdateDTO(BaseModel):
    new_status: IncidentStatus
    changed_by: Optional[str] = None
    comment: Optional[str] = None
