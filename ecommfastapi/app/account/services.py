from app.account.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.account.schemas import UserCreate, UserLogin
from app.account.utils import hash_password, verify_password, create_email_verification_token, verify_email_token_and_get_user_id

async def create_user(session: AsyncSession, user: UserCreate):
    stmt = select(User).where(User.email == user.email)
    result = await session.scalars(stmt)
    if result.first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    new_user = User(
        email = user.email,
        hashed_password = hash_password(user.password)
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user

async def authenticate_user(session: AsyncSession, user_login: UserLogin):
    stmt = select(User).where(User.email == user_login.email)
    result = await session.scalars(stmt)
    user = result.first()
    if not user or not verify_password(user_login.password, user.hashed_password):
        return None
    return user

async def email_verification_send(user: User):
    token = create_email_verification_token(user.id)
    link = f"http://localhost:8000/account/verify?token={token}"
    print("ABCD:", link)
    return {"msg": "Verification email sent"}

async def verify_email_token(session:AsyncSession, token: str):
    user_id = verify_email_token_and_get_user_id(token, "verify_email")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    stmt = select(User).where(User.id == user_id)
    result = await session.scalars(stmt)
    user = result.first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.is_verified == True:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified")
    
    user.is_verified = True
    session.add(user)
    await session.commit()
    return {"msg": "Email verified successfully"}
