from pydantic import BaseModel


class DashboardSummaryDTO(BaseModel):
    total_incidents: int
    critical_count: int
    high_count: int
    open_count: int
