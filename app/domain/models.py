from datetime import datetime
from sqlalchemy import Column, Index, Integer, String, Text, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_key = Column(String(80), unique=True, nullable=False)
    user_identifier = Column(String(80), nullable=True)
    user_ip = Column(String(45), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("ConversationMessage", back_populates="session")
    incidents = relationship("SecurityIncident", back_populates="session")


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("user_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    detected_as_suspicious = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("UserSession", back_populates="messages")


class DetectionRule(Base):
    __tablename__ = "detection_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), unique=True, nullable=False)
    pattern = Column(String(255), nullable=False)
    category = Column(String(40), nullable=False)
    severity = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)


class SecurityIncident(Base):
    __tablename__ = "security_incidents"

    id = Column(Integer, primary_key=True, index=True)
    incident_code = Column(String(40), unique=True, nullable=False)
    session_id = Column(Integer, ForeignKey("user_sessions.id"), nullable=False)
    category = Column(String(40), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    priority = Column(String(20), nullable=False)
    status = Column(String(30), nullable=False, index=True)
    confidence = Column(Float, default=0.0)
    detection_method = Column(String(60), nullable=False)
    input_text = Column(Text, nullable=False)
    output_text = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)

    session = relationship("UserSession", back_populates="incidents")
