import asyncio
import httpx
import random
from datetime import datetime

API_URL = "http://localhost:8000"

async def simulate_vitals(token: str):
    """Simulate realistic vital signs over time."""
    
    metrics = {
        "heart_rate": (60, 100),  # Normal range
        "glucose": (80, 120),
        "spo2": (95, 100),
    }
    
    async with httpx.AsyncClient() as client:
        for i in range(20):
            # Randomly pick a metric
            metric = random.choice(list(metrics.keys()))
            min_val, max_val = metrics[metric]
            
            # Occasionally generate abnormal values to trigger alerts
            if random.random() < 0.2:  # 20% chance of abnormal
                if metric == "heart_rate":
                    value = random.choice([random.randint(40, 50), random.randint(120, 140)])
                elif metric == "glucose":
                    value = random.choice([random.randint(60, 70), random.randint(180, 220)])
                else:
                    value = random.randint(85, 92)
            else:
                value = random.randint(min_val, max_val)
            
            response = await client.post(
                f"{API_URL}/vitals",
                json={"metric": metric, "value": value},
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                print(f"✓ Submitted: {metric} = {value}")
            else:
                print(f"✗ Error: {response.text}")
            
            await asyncio.sleep(2)  # Wait 2 seconds between readings

async def main():
    username = "test_patient"
    password = "test123"
    
    # Register or login
    async with httpx.AsyncClient() as client:
        # Try to register
        response = await client.post(
            f"{API_URL}/auth/register",
            json={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            print(f"✓ Registered as {username}")
            token = response.json()["access_token"]
        else:
            # Try to login
            response = await client.post(
                f"{API_URL}/auth/token",
                data={"username": username, "password": password}
            )
            if response.status_code == 200:
                print(f"✓ Logged in as {username}")
                token = response.json()["access_token"]
            else:
                print(f"✗ Failed to authenticate: {response.text}")
                return
    
    print("\nStarting vital signs simulation...")
    await simulate_vitals(token)

if __name__ == "__main__":
    asyncio.run(main())
