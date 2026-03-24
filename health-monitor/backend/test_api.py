import asyncio
import httpx
from main import app
from httpx import ASGITransport
import uuid

async def test_registration():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Generate a random username to ensure it doesn't exist
        random_user = f"user_{uuid.uuid4().hex[:8]}"

        print(f"Testing registration for new user: {random_user}")
        response = await client.post(
            "/auth/register",
            json={"username": random_user, "password": "password123"}
        )
        print("Registration Response Status:", response.status_code)
        print("Registration Response Body:", response.json())

        # Test duplicate registration
        print("\nTesting duplicate registration...")
        response2 = await client.post(
            "/auth/register",
            json={"username": random_user, "password": "password123"}
        )
        print("Duplicate Status:", response2.status_code)
        print("Duplicate Body:", response2.json())

if __name__ == "__main__":
    asyncio.run(test_registration())
