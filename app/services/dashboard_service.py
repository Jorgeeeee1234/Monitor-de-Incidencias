from app.domain.models import SecurityIncident


class DashboardService:
    def __init__(self, db):
        self.db = db

    def get_summary(self):
        incidents = self.db.query(SecurityIncident).all()

        return {
            "total_incidents": len(incidents),
            "critical_count": sum(1 for i in incidents if i.severity == "CRITICAL"),
            "high_count": sum(1 for i in incidents if i.severity == "HIGH"),
            "open_count": sum(1 for i in incidents if i.status not in {"RESOLVED", "CLOSED"}),
        }
