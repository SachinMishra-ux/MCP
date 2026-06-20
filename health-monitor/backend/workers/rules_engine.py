import asyncio
import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker

# Add parent directory to path so we can import models and database
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Vital, Alert, User
from database import DATABASE_URL

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Simple rule definitions
RULES = [
    {"metric": "heart_rate", "condition": "gt", "threshold": 120, "severity": "high"},
    {"metric": "heart_rate", "condition": "lt", "threshold": 50, "severity": "critical"},
    {"metric": "glucose", "condition": "gt", "threshold": 180, "severity": "high"},
    {"metric": "glucose", "condition": "lt", "threshold": 70, "severity": "critical"},
    {"metric": "spo2", "condition": "lt", "threshold": 90, "severity": "critical"},
]

def evaluate_rules(vital: Vital):
    """Check if vital triggers any alert rules."""
    triggered_alerts = []
    for rule in RULES:
        if rule["metric"] != vital.metric:
            continue
        
        if rule["condition"] == "gt" and vital.value > rule["threshold"]:
            triggered_alerts.append(rule)
        elif rule["condition"] == "lt" and vital.value < rule["threshold"]:
            triggered_alerts.append(rule)
    
    return triggered_alerts

async def process_vital_event(event_data: dict):
    """Process a single vital event from the stream."""
    try:
        vital_json = event_data.get("data")
        if not vital_json:
            return
        
        vital_dict = json.loads(vital_json)

        # Use model_validate so UUID and datetime strings are properly coerced.
        # Plain Vital(**vital_dict) fails because JSON has strings, not UUID/datetime.
        vital = Vital.model_validate(vital_dict)
        
        # Evaluate rules
        triggered = evaluate_rules(vital)
        
        if triggered:
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            async with async_session() as session:
                for rule in triggered:
                    # Build a human-friendly message per rule
                    direction = "above" if rule["condition"] == "gt" else "below"
                    message = (
                        f"{vital.metric.replace('_', ' ').title()} is {direction} threshold: "
                        f"{vital.value} (limit: {rule['threshold']})"
                    )
                    alert = Alert(
                        user_id=vital.user_id,
                        metric=vital.metric,
                        message=message,
                        severity=rule["severity"],
                        is_active=True,
                    )
                    session.add(alert)
                    print(f"[ALERT] {message} for user {vital.user_id}")
                    
                    # Publish each alert individually so the frontend receives
                    # a correctly-paired message + severity for every rule.
                    await redis_client.publish(
                        f"alerts:{str(vital.user_id)}",
                        json.dumps({
                            "metric": vital.metric,
                            "value": vital.value,
                            "severity": rule["severity"],
                            "message": message,
                        }),
                    )
                
                await session.commit()
    
    except Exception as e:
        print(f"Error processing event: {e}")
        traceback.print_exc()

async def worker():
    """Main worker loop that consumes from Redis Stream."""
    print("[WORKER] Starting vitals stream consumer...")
    
    # Create consumer group (ignore if exists)
    try:
        await redis_client.xgroup_create("vitals_stream", "workers", id="0", mkstream=True)
    except redis.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise
    
    consumer_name = "worker-1"
    
    while True:
        try:
            # Read from stream
            messages = await redis_client.xreadgroup(
                "workers",
                consumer_name,
                {"vitals_stream": ">"},
                count=10,
                block=1000  # 1 second timeout
            )
            
            for stream_name, stream_messages in messages:
                for message_id, event_data in stream_messages:
                    await process_vital_event(event_data)
                    # Acknowledge message
                    await redis_client.xack("vitals_stream", "workers", message_id)
        
        except Exception as e:
            print(f"Worker error: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(worker())
