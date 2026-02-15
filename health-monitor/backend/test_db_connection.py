import asyncio
import os
from database import engine

async def test_connection():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda _: print("Connection via SQLAlchemy successful!"))
        print("Database connection Verified!")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
