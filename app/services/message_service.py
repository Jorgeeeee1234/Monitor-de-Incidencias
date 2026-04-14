import logging

from sqlalchemy.orm import Session
from app.domain.models import ConversationMessage
from app.services.session_service import SessionService
from app.services.rule_engine_service import RuleEngineService
from app.services.llm_service import LLMService
from app.services.incident_service import IncidentService

logger = logging.getLogger(__name__)


class MessageService:
    def __init__(self, db: Session):
        self.db = db
        self.session_service = SessionService(db)
        self.rule_engine = RuleEngineService()
        self.llm_service = LLMService()
        self.incident_service = IncidentService(db)

    def analyze_message(self, dto):
        session = self.session_service.get_by_key(dto.session_key)
        if not session:
            raise ValueError("Session not found")

        selected_detectors = dto.detectors
        detection_input = self.rule_engine.detect(dto.content, detectors=selected_detectors)

        assistant_text = self.llm_service.generate_response(dto.content)
        detection_output = self.rule_engine.detect(assistant_text, detectors=selected_detectors)

        incident = None
        final_detection = detection_input if detection_input["matched"] else None
        if not final_detection and detection_output["matched"]:
            final_detection = detection_output

        try:
            user_message = ConversationMessage(
                session_id=session.id,
                role="USER",
                content=dto.content,
                detected_as_suspicious=detection_input["matched"]
            )
            assistant_message = ConversationMessage(
                session_id=session.id,
                role="ASSISTANT",
                content=assistant_text,
                detected_as_suspicious=detection_output["matched"]
            )
            self.db.add_all([user_message, assistant_message])

            if final_detection:
                incident = self.incident_service.create_incident(
                    session=session,
                    detection=final_detection,
                    input_text=dto.content,
                    output_text=assistant_text,
                    commit=False,
                    write_log=False,
                )

            self.db.commit()
            if incident:
                self.db.refresh(incident)
        except Exception:
            self.db.rollback()
            raise

        if incident:
            try:
                self.incident_service.write_incident_log(incident)
            except OSError:
                logger.exception("Failed to write incident log for %s", incident.incident_code)

        return {
            "session_key": session.session_key,
            "assistant_response": assistant_text,
            "incident_detected": incident is not None,
            "input_detected": detection_input["matched"],
            "output_detected": detection_output["matched"],
            "detectors_used": detection_input.get("detectors_applied", []),
            "incident_id": incident.id if incident else None,
            "incident_code": incident.incident_code if incident else None,
            "category": final_detection["category"] if final_detection else None,
            "severity": final_detection["severity"] if final_detection else None,
        }
