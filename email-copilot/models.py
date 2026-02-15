from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID, uuid4

class EmailMetadata(BaseModel):
    id: str
    thread_id: str
    subject: str
    sender: str
    recipient: str
    timestamp: datetime
    summary: str
    is_unread: bool = True

class EmailThread(BaseModel):
    id: str
    emails: List[EmailMetadata]

class DraftReply(BaseModel):
    email_id: str
    content: str
    tone: str
    mimicked_style_id: Optional[str] = None

class WritingStyle(BaseModel):
    profile_name: str = "default"
    formality: float = 0.5  # 0 to 1
    brevity: float = 0.5    # 0 to 1
    preferred_greetings: List[str] = ["Hi", "Hello"]
    preferred_closings: List[str] = ["Best,", "Regards,"]
    tone_markers: List[str] = []

class StyleUpdate(BaseModel):
    email_id: str
    original_draft: str
    final_email: str
