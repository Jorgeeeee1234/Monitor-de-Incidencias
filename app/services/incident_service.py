from datetime import datetime
import json
import uuid
from pathlib import Path
from sqlalchemy.orm import Session
from app.domain.enums import IncidentStatus
from app.domain.models import SecurityIncident


class IncidentService:
    def __init__(self, db: Session):
        self.db = db
        self.log_path = Path("logs/incidents.jsonl")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def _map_priority(self, severity: str) -> str:
        mapping = {
            "CRITICAL": "URGENT",
            "HIGH": "HIGH",
            "MEDIUM": "MEDIUM",
            "LOW": "LOW",
            "INFO": "LOW",
        }
        return mapping.get(severity, "LOW")

    def _generate_incident_code(self) -> str:
        return f"INC-{uuid.uuid4().hex}"

    def create_incident(
        self,
        session,
        detection,
        input_text: str,
        output_text: str | None,
        commit: bool = True,
        write_log: bool = True,
    ):
        incident = SecurityIncident(
            incident_code=self._generate_incident_code(),
            session_id=session.id,
            category=detection["category"],
            severity=detection["severity"],
            priority=self._map_priority(detection["severity"]),
            status=IncidentStatus.DETECTED.value,
            confidence=detection["confidence"],
            detection_method=detection["detection_method"],
            input_text=input_text,
            output_text=output_text,
            notes=f"Regla detectada: {detection['rule_name']}"
        )

        self.db.add(incident)
        self.db.flush()

        if commit:
            self.db.commit()
            self.db.refresh(incident)
            if write_log:
                self._write_jsonl(incident)
        return incident

    def _write_jsonl(self, incident):
        data = {
            "incident_code": incident.incident_code,
            "session_id": incident.session_id,
            "category": incident.category,
            "severity": incident.severity,
            "priority": incident.priority,
            "status": incident.status,
            "confidence": incident.confidence,
            "detection_method": incident.detection_method,
            "input_text": incident.input_text,
            "output_text": incident.output_text,
            "notes": incident.notes,
            "created_at": incident.created_at.isoformat() if incident.created_at else None,
        }

        with open(self.log_path, "a", encoding="utf-8") as file:
            file.write(json.dumps(data, ensure_ascii=False) + "\n")

    def write_incident_log(self, incident):
        self._write_jsonl(incident)

    def list_incidents(self, severity=None, category=None, status=None):
        query = self.db.query(SecurityIncident)

        if severity:
            query = query.filter(SecurityIncident.severity == severity)
        if category:
            query = query.filter(SecurityIncident.category == category)
        if status:
            query = query.filter(SecurityIncident.status == status)

        return query.order_by(SecurityIncident.created_at.desc()).all()

    def get_incident(self, incident_id: int):
        return self.db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()

    def update_status(self, incident, dto):
        new_status = getattr(dto.new_status, "value", str(dto.new_status))
        allowed_statuses = {status.value for status in IncidentStatus}
        if new_status not in allowed_statuses:
            raise ValueError(f"Invalid incident status: {new_status}")

        incident.status = new_status
        if new_status in {IncidentStatus.RESOLVED.value, IncidentStatus.CLOSED.value}:
            incident.resolved_at = datetime.utcnow()
        incident.notes = dto.comment or incident.notes
        self.db.commit()
        self.db.refresh(incident)
        return incident
