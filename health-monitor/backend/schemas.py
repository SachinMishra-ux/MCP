from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: UUID

class TokenData(BaseModel):
    username: Optional[str] = None

class VitalCreate(BaseModel):
    metric: str
    value: float
    device_id: Optional[UUID] = None
    timestamp: Optional[datetime] = None

class VitalResponse(VitalCreate):
    id: UUID
    user_id: UUID
    timestamp: datetime
