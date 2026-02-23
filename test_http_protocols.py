import asyncio
import httpx
import traceback
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamable_http_client
from mcp import ClientSession

async def test_sse(url):
    print(f"Testing SSE: {url}")
    try:
        async with sse_client(url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                print("SSE Success Tools:", tools)
    except Exception as e:
        print("SSE Error:", type(e))
        traceback.print_exc()

async def test_streamable(url):
    print(f"Testing Streamable: {url}")
    try:
        async with streamable_http_client(url, http_client=httpx.AsyncClient(timeout=30)) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                print("Streamable Success Tools:", tools)
    except Exception as e:
        print("Streamable Error:", type(e))
        traceback.print_exc()

async def main():
    url_base = "https://salary-prediction-mcp-server.fastmcp.app"
    await test_sse(f"{url_base}/sse")
    await test_streamable(f"{url_base}/mcp")

if __name__ == "__main__":
    asyncio.run(main())
