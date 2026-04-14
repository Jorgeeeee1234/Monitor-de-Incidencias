from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class SessionCreateDTO(BaseModel):
    user_identifier: Optional[str] = None
    user_ip: Optional[str] = None


class SessionResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_key: str
    user_identifier: Optional[str]
    user_ip: Optional[str]
    started_at: datetime
