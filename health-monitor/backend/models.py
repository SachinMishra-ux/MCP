from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship, Column, DateTime

class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    role: str = "patient"  # patient, doctor, admin

class Vital(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    metric: str = Field(index=True)  # heart_rate, glucose, spo2
    value: float
    timestamp: datetime = Field(
        sa_column=Column(DateTime(timezone=True), index=True, nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )

class Alert(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    metric: str
    message: str
    severity: str = "medium"  # low, medium, high, critical
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    is_active: bool = True
