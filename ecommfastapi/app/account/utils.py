from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from decouple import config
from jose import jwt, ExpiredSignatureError, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from app.account.models import User, RefreshToken
from typing import Optional, Any
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from sqlalchemy import select

JWT_SECRET_KEY = config("JWT_SECRET_KEY")
JWT_ALGORITHM = config("JWT_ALGORITHM")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = config("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", default=30, cast=int)
JWT_REFRESH_TOKEN_EXPIRE_DAYS = config("JWT_REFRESH_TOKEN_EXPIRE_DAYS", default=7, cast=int)

EMAIL_VERIFICATION_TOKEN_TIME_HOUR = config("EMAIL_VERIFICATION_TOKEN_TIME_HOUR", default=1, cast=int)
PASSWORD_RESET_TOKEN_TIME_HOUR = config("PASSWORD_RESET_TOKEN_TIME_HOUR", default=2, cast=int)

pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    
    to_encode = data.copy()
    if expires_delta:
        expires_delta = datetime.now(timezone.utc) + expires_delta
    else:
        expires_delta = datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expires_delta})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def create_tokens(session: AsyncSession, user: User):
    access_token = create_access_token(data={"sub": str(user.id)})
    
    refresh_token_str = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = RefreshToken(
        user_id=user.id,
        token=refresh_token_str,
        expires_at=expires_at
    )
    session.add(refresh_token)
    await session.commit()
    return {"access_token": access_token, "refresh_token": refresh_token_str, "token_type": "bearer"}

def success_response(message: str, data: Optional[Any] = None, status_code: int = 200):
    response = {
        "success": True,
        "status_code": status_code,
        "message": message
    }
    if data is not None:
        response["data"] = data

    return JSONResponse(
        content=response,
        status_code=status_code
    )

def error_response(message: str, status_code: int = 400, errors: Optional[Any] = None):
    response = {
        "success": False,
        "status_code": status_code,
        "message": message
    }

    if errors is not None:
        response["errors"] = errors

    return JSONResponse(
        content=response,
        status_code=status_code
    )

def decode_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=JWT_ALGORITHM)
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
async def verify_refresh_token(session: AsyncSession, token: str):
    stmt = select(RefreshToken).where(RefreshToken.token == token)
    result = await session.scalars(stmt)
    db_refresh_token = result.first()

    if db_refresh_token and not db_refresh_token.revoked:
        expires_at = db_refresh_token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at > datetime.now(timezone.utc):
            user_stmt = select(User).where(User.id == db_refresh_token.user_id)
            user_result = await session.scalars(user_stmt)
            return user_result.first()
        
    return None

def create_email_verification_token(user_id: int):
    expire = datetime.now(timezone.utc) + timedelta(hours=EMAIL_VERIFICATION_TOKEN_TIME_HOUR)
    to_encode = {"sub": str(user_id), "type": "verify_email", "exp": expire}
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_email_token_and_get_user_id(token: str, token_type: str):
    payload = decode_token(token)
    if not payload or payload.get("type") != token_type:
        return None
    return int(payload.get("sub"))

async def get_user_by_email(session: AsyncSession, email: str):
    stmt = select(User).where(User.email == email)
    result = await session.scalars(stmt)
    return result.first() 

def create_password_reset_token(user_id: int):
    expire = datetime.now(timezone.utc) + timedelta(hours=PASSWORD_RESET_TOKEN_TIME_HOUR)
    to_encode = {"sub": str(user_id), "type": "password_reset", "exp": expire}
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
