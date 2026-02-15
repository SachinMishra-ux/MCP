from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

# robustly construct the URL
user = os.getenv("DB_USER", "postgres")
password = os.getenv("DB_PASSWORD", "")
host = os.getenv("DB_HOST", "localhost")
port = os.getenv("DB_PORT", "5432")
db_name = os.getenv("DB_NAME", "postgres")

# URL encode the password and user
encoded_user = quote_plus(user)
encoded_password = quote_plus(password)

DATABASE_URL = f"postgresql+asyncpg://{encoded_user}:{encoded_password}@{host}:{port}/{db_name}"

engine = create_async_engine(DATABASE_URL, echo=False, future=True)

async def init_db():
    async with engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all) # Uncomment to reset DB
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncSession:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
