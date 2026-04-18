from sqlalchemy import func, not_
from app.domain.models import SecurityIncident


class DashboardService:
    def __init__(self, db):
        self.db = db

    def get_summary(self):
        total = self.db.query(func.count(SecurityIncident.id)).scalar()
        critical = self.db.query(func.count(SecurityIncident.id)).filter(
            SecurityIncident.severity == "CRITICAL"
        ).scalar()
        high = self.db.query(func.count(SecurityIncident.id)).filter(
            SecurityIncident.severity == "HIGH"
        ).scalar()
        open_count = self.db.query(func.count(SecurityIncident.id)).filter(
            not_(SecurityIncident.status.in_(["RESOLVED", "CLOSED"]))
        ).scalar()

        return {
            "total_incidents": total,
            "critical_count": critical,
            "high_count": high,
            "open_count": open_count,
        }
