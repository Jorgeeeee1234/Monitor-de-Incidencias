from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dto.history_dto import DashboardSummaryDTO
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/summary", response_model=DashboardSummaryDTO)
def get_summary(db: Session = Depends(get_db)):
    return DashboardService(db).get_summary()
