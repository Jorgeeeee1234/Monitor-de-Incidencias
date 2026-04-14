from enum import Enum


class IncidentCategory(str, Enum):
    PROMPT_INJECTION = "PROMPT_INJECTION"
    DATA_LEAK = "DATA_LEAK"
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"
    RESPONSE_MANIPULATION = "RESPONSE_MANIPULATION"


class IncidentSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, Enum):
    DETECTED = "DETECTED"
    IN_ANALYSIS = "IN_ANALYSIS"
    CONFIRMED = "CONFIRMED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
