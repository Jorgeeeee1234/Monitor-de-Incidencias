import uuid
from sqlalchemy.orm import Session
from app.domain.models import UserSession


class SessionService:
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, dto):
        session = UserSession(
            session_key=str(uuid.uuid4()),
            user_identifier=dto.user_identifier,
            user_ip=dto.user_ip
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_by_key(self, session_key: str):
        return (
            self.db.query(UserSession)
            .filter(UserSession.session_key == session_key)
            .first()
        )
