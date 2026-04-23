from typing import Optional

from pydantic import BaseModel, Field


class PromptCheckAnalyzeDTO(BaseModel):
    content: str
    detectors: Optional[list[str]] = None
    model: Optional[str] = None


class PromptCheckAnalyzeResponseDTO(BaseModel):
    incident_detected: bool
    input_detected: bool
    output_detected: bool
    detectors_used: list[str] = Field(default_factory=list)
    category: Optional[str] = None
    severity: Optional[str] = None
    rule_name: Optional[str] = None
    detection_method: Optional[str] = None


class PromptCheckMatchDTO(BaseModel):
    detector_triggered: str
    rule_name: str
    category: str
    severity: str
    confidence: float
    detection_method: str


class PromptCheckAnalyzeMultiMatchResponseDTO(BaseModel):
    incident_detected: bool
    input_detected: bool
    output_detected: bool
    detectors_used: list[str] = Field(default_factory=list)
    match_count: int = 0
    matches: list[PromptCheckMatchDTO] = Field(default_factory=list)
    top_match: Optional[PromptCheckMatchDTO] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    rule_name: Optional[str] = None
    detection_method: Optional[str] = None
