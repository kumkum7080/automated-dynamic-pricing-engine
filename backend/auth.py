import os
from datetime import datetime, timedelta
from typing import Optional
import jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyCookie, HTTPBearer, HTTPAuthorizationCredentials
from backend.db import db_session


# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey_change_me_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

# Auth schemes
cookie_scheme = APIKeyCookie(name="access_token", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)

def verify_password(plain_password, hashed_password):
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def get_password_hash(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": int(expire.timestamp())})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(
    cookie_token: Optional[str] = Depends(cookie_scheme),
    bearer_token: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
):
    token = None
    if bearer_token:
        token = bearer_token.credentials
    elif cookie_token:
        if cookie_token.startswith("Bearer "):
            token = cookie_token[7:]
        else:
            token = cookie_token

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        user_id: int = payload.get("user_id")
        if username is None or user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    # Verify user still exists in database
    with db_session() as cursor:
        cursor.execute("SELECT user_id, username, role FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        if user is None:
            raise credentials_exception
        return user

