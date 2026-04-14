from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dto.incident_dto import IncidentResponseDTO, IncidentStatusUpdateDTO
from app.services.incident_service import IncidentService

router = APIRouter()


@router.get("", response_model=list[IncidentResponseDTO])
def list_incidents(
    severity: str | None = Query(default=None),
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return IncidentService(db).list_incidents(severity, category, status)


@router.get("/{incident_id}", response_model=IncidentResponseDTO)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = IncidentService(db).get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.patch("/{incident_id}/status", response_model=IncidentResponseDTO)
def update_incident_status(
    incident_id: int,
    dto: IncidentStatusUpdateDTO,
    db: Session = Depends(get_db),
):
    service = IncidentService(db)
    incident = service.get_incident(incident_id)

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    return service.update_status(incident, dto)
