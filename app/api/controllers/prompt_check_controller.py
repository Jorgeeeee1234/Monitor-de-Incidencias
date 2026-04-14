from fastapi import APIRouter, HTTPException

from app.dto.prompt_check_dto import (
    PromptCheckAnalyzeDTO,
    PromptCheckAnalyzeMultiMatchResponseDTO,
    PromptCheckAnalyzeResponseDTO,
)
from app.services.prompt_check_service import PromptCheckService

router = APIRouter()


@router.get("/detectors")
def list_detectors():
    return {"detectors": PromptCheckService().get_available_detectors()}


@router.post("/analyze", response_model=PromptCheckAnalyzeResponseDTO)
def analyze_input(dto: PromptCheckAnalyzeDTO):
    service = PromptCheckService()
    try:
        return service.analyze_input(dto.content, dto.detectors)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(exc)}")


@router.post("/analyze-multimatch", response_model=PromptCheckAnalyzeMultiMatchResponseDTO)
def analyze_input_multimatch(dto: PromptCheckAnalyzeDTO):
    service = PromptCheckService()
    try:
        return service.analyze_input_multimatch(dto.content, dto.detectors)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(exc)}")
