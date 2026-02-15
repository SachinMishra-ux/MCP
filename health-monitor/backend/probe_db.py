import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from urllib.parse import quote_plus
import os

candidates = [
    # (user, password, db, host)
    ("postgres", "Postgres@#123$", "postgres", "127.0.0.1"),
    ("postgres", "postgres", "postgres", "127.0.0.1"),
    ("postgres", "", "postgres", "127.0.0.1"),
    ("sachinmishra", "", "postgres", "127.0.0.1"), # often default on brew
    ("sachinmishra", "Postgres@#123$", "postgres", "127.0.0.1"),
]

async def probe():
    for user, pwd, db, host in candidates:
        encoded_pwd = quote_plus(pwd) if pwd else ""
        url = f"postgresql+asyncpg://{user}:{encoded_pwd}@{host}:5432/{db}"
        print(f"Trying: user={user}, pwd={'***' if pwd else 'EMPTY'}, db={db}")
        
        try:
            engine = create_async_engine(url, echo=False)
            async with engine.begin() as conn:
                await conn.run_sync(lambda _: print("  -> SUCCESS!"))
            print(f"  -> FOUND VALID CREDENTIALS: {url}")
            return
        except Exception as e:
            print(f"  -> Failed: {str(e).splitlines()[0]}")

if __name__ == "__main__":
    asyncio.run(probe())
