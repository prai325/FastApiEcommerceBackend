from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import JSONResponse
from app.account.schemas import UserCreate, UserOut, UserLogin
from app.account.services import create_user, authenticate_user, email_verification_send, verify_email_token
from app.db.config import SessionDep
from app.account.utils import create_tokens, success_response, error_response, verify_refresh_token
from app.account.models import User
from app.account.dep import get_current_user

router = APIRouter()

@router.post("/register")
async def register(session: SessionDep, user: UserCreate):
    new_user = await create_user(session, user)
    user_out = UserOut.model_validate(new_user)
    return success_response(
        message="User registered successfully",
        data=user_out.model_dump(),
        status_code=201
    )
    
@router.post("/login")
async def login(session: SessionDep, user: UserLogin):
    authenticated_user = await authenticate_user(session, user)
    if not authenticated_user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    tokens = await create_tokens(session, authenticated_user)

    # Convert ORM `User` to serializable dict using `UserOut` (pydantic v2 `from_attributes`).
    user_out = UserOut.model_validate(authenticated_user)
    content = {"message": "Login successful", "tokens": tokens, "user": user_out.model_dump()}

    response = success_response(
        message="Login successful",
        data={
            "tokens": tokens,
            "user": user_out.model_dump()  
        },
        status_code=200
    )
    response.set_cookie(key="access_token", value=tokens["access_token"], httponly=True, secure=True, samesite="Lax", max_age=1800)
    response.set_cookie(key="refresh_token", value=tokens["refresh_token"], httponly=True, secure=True, samesite="Lax", max_age=604800)
    return response
    
@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    user_out = UserOut.model_validate(user)
    response = success_response(
        message="Successful get user",
        data={
            "user": user_out.model_dump()  
        },
        status_code=200
    )
    return response

@router.post("/refresh")
async def refresh_token(session: SessionDep, request: Request):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    
    user = await verify_refresh_token(session, token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    
    tokens = await create_tokens(session, user)
    response = success_response(
        message="Token refreshed successfully",
        data=None,
        status_code=200
    )
    response.set_cookie(key="access_token", value=tokens["access_token"], httponly=True, secure=True, samesite="Lax", max_age=1800)
    response.set_cookie(key="refresh_token", value=tokens["refresh_token"], httponly=True, secure=True, samesite="Lax", max_age=604800)
    return response

@router.post("/send-verification-email")
async def send_verification_email(user: User = Depends(get_current_user)):
    return await email_verification_send(user)

@router.get("/verify-email")
async def verify_email(session: SessionDep, token: str):
        return await verify_email_token(session, token)
   