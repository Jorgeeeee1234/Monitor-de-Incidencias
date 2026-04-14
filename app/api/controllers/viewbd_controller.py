from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.viewbd_service import ViewBDService

router = APIRouter()


@router.get("/tables")
def list_tables(db: Session = Depends(get_db)):
    return ViewBDService(db).list_tables()


@router.get("/tables/{table_name}")
def get_table_rows(
    table_name: str,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    service = ViewBDService(db)
    try:
        return service.get_table_rows(table_name, limit)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
