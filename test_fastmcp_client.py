import asyncio
from fastmcp import Client

async def main():
    print("Testing /mcp")
    client1 = Client("https://salary-prediction-mcp-server.fastmcp.app/mcp")
    try:
        async with client1:
            await client1.ping()
            print("Ping /mcp success!")
    except Exception as e:
        print(f"Error /mcp: {type(e)} {e}")

    print("\nTesting /sse")
    client2 = Client("https://salary-prediction-mcp-server.fastmcp.app/sse")
    try:
        async with client2:
            await client2.ping()
            print("Ping /sse success!")
    except Exception as e:
        print(f"Error /sse: {type(e)} {e}")

asyncio.run(main())
