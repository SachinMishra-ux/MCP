"""
Script to create a test user in the database
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select, SQLModel
from models import User
from auth import get_password_hash
from database import DATABASE_URL, engine
import sys

async def create_test_user():
    """Create a test user for development"""
    username = "test_patient"
    password = "test123"
    
    # Initialize database tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if user already exists
        statement = select(User).where(User.username == username)
        result = await session.exec(statement)
        existing_user = result.first()
        
        if existing_user:
            print(f"✓ User '{username}' already exists")
            print(f"  User ID: {existing_user.id}")
            print(f"  Role: {existing_user.role}")
            return
        
        # Create new user
        hashed_password = get_password_hash(password)
        new_user = User(
            username=username,
            password_hash=hashed_password,
            role="patient"
        )
        
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        
        print(f"✓ Created user '{username}'")
        print(f"  User ID: {new_user.id}")
        print(f"  Password: {password}")
        print(f"  Role: {new_user.role}")

if __name__ == "__main__":
    try:
        asyncio.run(create_test_user())
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
