from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dto.session_dto import SessionCreateDTO, SessionResponseDTO
from app.services.session_service import SessionService

router = APIRouter()


@router.post("", response_model=SessionResponseDTO)
def create_session(dto: SessionCreateDTO, db: Session = Depends(get_db)):
    return SessionService(db).create_session(dto)


@router.get("/{session_key}", response_model=SessionResponseDTO)
def get_session(session_key: str, db: Session = Depends(get_db)):
    session = SessionService(db).get_by_key(session_key)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
