from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dto.message_dto import MessageAnalyzeDTO, MessageAnalyzeResponseDTO
from app.services.ai_classifier_service import AIClassifierUnavailableError
from app.services.message_service import MessageService
from app.services.rule_engine_service import RuleEngineService

router = APIRouter()


@router.get("/detectors")
def list_detectors():
    return {"detectors": RuleEngineService().get_available_detectors()}


@router.post("/analyze", response_model=MessageAnalyzeResponseDTO)
def analyze_message(dto: MessageAnalyzeDTO, db: Session = Depends(get_db)):
    service = MessageService(db)
    try:
        return service.analyze_message(dto)
    except ValueError as exc:
        detail = str(exc)
        if detail == "Session not found":
            raise HTTPException(status_code=404, detail=detail)
        raise HTTPException(status_code=400, detail=detail)
    except AIClassifierUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(exc)}")
