"""
BusinessVerse - FastAPI Authentication Utilities
Handles JWT token generation, verification, and password checks.
"""

import hashlib
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

SECRET_KEY = "businessverse_super_secret_jwt_key_change_in_production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 Hours

# Existing user store
USERS = {
    "admin":   hashlib.sha256("admin123".encode()).hexdigest(),
    "analyst": hashlib.sha256("analyst123".encode()).hexdigest(),
    "viewer":  hashlib.sha256("viewer123".encode()).hexdigest(),
}

USER_ROLES = {
    "admin":   "Administrator",
    "analyst": "Business Analyst",
    "viewer":  "Viewer",
}

security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash password using SHA-256 (matches original Streamlit auth)."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_credentials(username: str, password_raw: str) -> dict:
    """Verify raw password against users and return user details or None."""
    hashed = hash_password(password_raw)
    if username in USERS and USERS[username] == hashed:
        return {
            "username": username,
            "role": USER_ROLES.get(username, "Viewer")
        }
    return None


def create_access_token(data: dict) -> str:
    """Generate a JWT access token containing user metadata and expiry."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decode a JWT access token and return payload, or raise exception if invalid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """Dependency that extracts JWT from bearer header and returns payload."""
    token = credentials.credentials
    return decode_access_token(token)
