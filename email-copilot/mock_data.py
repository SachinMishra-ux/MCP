from datetime import datetime, timedelta
from typing import List, Dict
from models import EmailMetadata

# Mock Database
MOCK_EMAILS: Dict[str, EmailMetadata] = {
    "email_1": EmailMetadata(
        id="email_1",
        thread_id="thread_1",
        subject="Project Update Request",
        sender="boss@example.com",
        recipient="me@example.com",
        timestamp=datetime.now() - timedelta(hours=2),
        summary="Urgent: Need the status of the Q1 project by EOD.",
        is_unread=True
    ),
    "email_2": EmailMetadata(
        id="email_2",
        thread_id="thread_2",
        subject="Dinner Plans?",
        sender="friend@personal.com",
        recipient="me@example.com",
        timestamp=datetime.now() - timedelta(days=1),
        summary="Checking in to see if you are free for dinner on Friday.",
        is_unread=True
    ),
    "email_3": EmailMetadata(
        id="email_3",
        thread_id="thread_3",
        subject="Subscription Renewal",
        sender="billing@service.com",
        recipient="me@example.com",
        timestamp=datetime.now() - timedelta(minutes=45),
        summary="Your subscription will automatically renew in 2 days.",
        is_unread=True
    )
}

def get_unread_emails() -> List[EmailMetadata]:
    return [e for e in MOCK_EMAILS.values() if e.is_unread]

def get_email_by_id(email_id: str) -> EmailMetadata:
    return MOCK_EMAILS.get(email_id)
