from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import bcrypt
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from database import get_session
from models import User
from schemas import Token, TokenData, UserLogin
import os

SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

auth_router = APIRouter()

# Global token for MCP server fallback
_mcp_token: Optional[str] = None

def set_mcp_token(token: str):
    global _mcp_token
    _mcp_token = token

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)):
    # Fallback to global MCP token if the provided token is missing or default
    if (not token or token == "undefined") and _mcp_token:
        token = _mcp_token
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        if token is None:
            raise credentials_exception
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    statement = select(User).where(User.username == token_data.username)
    result = await session.exec(statement)
    user = result.first()
    if user is None:
        raise credentials_exception
    return user

@auth_router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):
    statement = select(User).where(User.username == form_data.username)
    result = await session.exec(statement)
    user = result.first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    set_mcp_token(access_token)
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}

@auth_router.post("/token/json", response_model=Token)
async def login_json(user_in: UserLogin, session: AsyncSession = Depends(get_session)):
    """JSON-based login for MCP clients that don't support form-data."""
    statement = select(User).where(User.username == user_in.username)
    result = await session.exec(statement)
    user = result.first()
    
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    access_token = create_access_token(data={"sub": user.username})
    set_mcp_token(access_token)
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}

@auth_router.post("/register", response_model=Token)
async def register_user(user_in: UserLogin, session: AsyncSession = Depends(get_session)):
    # Check if user exists
    statement = select(User).where(User.username == user_in.username)
    result = await session.exec(statement)
    if result.first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user_in.password)
    new_user = User(username=user_in.username, password_hash=hashed_password, role="patient")
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    
    access_token = create_access_token(data={"sub": new_user.username})
    set_mcp_token(access_token)
    return {"access_token": access_token, "token_type": "bearer", "user_id": new_user.id}
