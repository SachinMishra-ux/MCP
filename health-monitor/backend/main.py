from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from database import init_db, get_session
from models import Vital, Alert, User
from schemas import VitalCreate, VitalResponse
from auth import auth_router, get_current_user
from contextlib import asynccontextmanager
import asyncio
import json
import redis.asyncio as redis
import os
from datetime import datetime, timezone

# Redis Connection
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await redis_client.close()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(lifespan=lifespan)

# Add CORS middleware to allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; in production, use ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])

# --- Ingestion Endpoint ---
@app.post("/vitals", response_model=VitalResponse)
async def ingest_vital(
    vital_in: VitalCreate, 
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # Create DB model from schema
    # We dump the input and inject the user_id before validation
    # We also remove timestamp if it's None to let the default_factory handle it
    vital_data = vital_in.model_dump(exclude_none=True)
    vital_data["user_id"] = current_user.id
    
    vital = Vital.model_validate(vital_data)
    
    # 1. Save to DB (Async)
    session.add(vital)
    await session.commit()
    await session.refresh(vital)
    
    # 2. Publish to Redis Stream for Workers
    # We serialize the full vital object including ID and user_id
    event_data = vital.model_dump_json()
    await redis_client.xadd("vitals_stream", {"data": event_data})
    
    # 3. Publish to Redis Pub/Sub for Realtime Frontend
    await redis_client.publish(f"vitals_live:{str(current_user.id)}", event_data)
    
    return vital

# --- Real-time WebSocket ---
@app.websocket("/ws/vitals/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    pubsub = redis_client.pubsub()
    
    # Subscribe to both vitals and alerts
    await pubsub.subscribe(f"vitals_live:{user_id}", f"alerts:{user_id}")
    
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                channel = message["channel"]
                data = json.loads(message["data"])
                
                # Determine type based on channel
                msg_type = "vital" if "vitals_live" in channel else "alert"
                
                await websocket.send_json({
                    "type": msg_type,
                    "data": data
                })
            await asyncio.sleep(0.01)
    except WebSocketDisconnect:
        await pubsub.unsubscribe()
    except Exception as e:
        print(f"WS Error: {e}")
        await pubsub.unsubscribe()

# --- Simple Getter for MCP ---
@app.get("/vitals", response_model=list[VitalResponse])
async def get_my_vitals(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    statement = select(Vital).where(Vital.user_id == current_user.id).order_by(Vital.timestamp.desc()).limit(10)
    result = await session.exec(statement)
    return result.all()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
