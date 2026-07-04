from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.db import get_db
from auth.models import User, APIKey
from auth.schemas import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserResponse,
    APIKeyCreate,
    APIKeyResponse,
    APIKeyCreatedResponse,
)
from auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    generate_api_key,
    get_current_user,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check existing username
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    # Check existing email
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: Session = Depends(get_db)):
    """Login and receive JWT token + API key."""
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Create JWT token
    access_token = create_access_token(user.id, user.username)

    # Get or create default API key
    api_key_obj = db.query(APIKey).filter(
        APIKey.user_id == user.id, APIKey.is_active == True
    ).first()
    if not api_key_obj:
        api_key_obj = APIKey(
            key=generate_api_key(),
            name="Default Key",
            user_id=user.id,
        )
        db.add(api_key_obj)
        db.commit()
        db.refresh(api_key_obj)

    return TokenResponse(
        access_token=access_token,
        api_key=api_key_obj.key,
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return current_user


@router.post("/api-keys", response_model=APIKeyCreatedResponse, status_code=201)
async def create_api_key(
    data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a new API key for the authenticated user."""
    new_key = generate_api_key()
    api_key_obj = APIKey(
        key=new_key,
        name=data.name,
        user_id=current_user.id,
    )
    db.add(api_key_obj)
    db.commit()
    return APIKeyCreatedResponse(api_key=new_key, name=data.name)


@router.get("/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all API keys for the authenticated user."""
    keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()
    return [
        APIKeyResponse(
            id=k.id,
            name=k.name,
            key_prefix=k.key[:12] + "...",
            is_active=k.is_active,
            created_at=k.created_at,
        )
        for k in keys
    ]


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke an API key."""
    key = db.query(APIKey).filter(
        APIKey.id == key_id, APIKey.user_id == current_user.id
    ).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    key.is_active = False
    db.commit()
    return {"message": "API key revoked successfully"}
