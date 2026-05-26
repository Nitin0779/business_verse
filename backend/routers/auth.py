"""
BusinessVerse - FastAPI Authentication Router
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from utils.auth import verify_credentials, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """Authenticate credentials and return a secure JWT token."""
    user = verify_credentials(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user["username"],
        "role": user["role"]
    }


@router.get("/verify")
def verify_token(current_user: dict = Depends(get_current_user)):
    """Simple connection validation token check."""
    return {"status": "authenticated", "username": current_user["sub"], "role": current_user["role"]}
