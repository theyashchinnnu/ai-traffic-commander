import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy.orm import Session

from config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_HOURS
from database.db import get_db
from auth.models import User, APIKey

security = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = uuid.uuid4().hex
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() + ":" + salt


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    stored_hash, salt = hashed.rsplit(":", 1)
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == stored_hash


def create_access_token(user_id: str, username: str) -> str:
    """Create JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "sub": user_id,
        "username": username,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def generate_api_key() -> str:
    """Generate a unique API key."""
    return f"tc_{uuid.uuid4().hex}{uuid.uuid4().hex[:16]}"


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    api_key: Optional[str] = Security(api_key_header),
    db: Session = Depends(get_db),
) -> User:
    """Authenticate user via JWT token OR API key."""
    # Try API key first
    if api_key:
        db_key = db.query(APIKey).filter(APIKey.key == api_key, APIKey.is_active == True).first()
        if db_key:
            return db_key.user

    # Try JWT token
    if credentials:
        payload = verify_token(credentials.credentials)
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if user:
            return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication. Provide a valid JWT token or API key.",
        headers={"WWW-Authenticate": "Bearer"},
    )
