"""
Auth router — /api/auth/signup and /login (§5).
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_database
from app.auth import hash_password, verify_password, create_access_token
from app.models.user import UserCreate, UserLogin, AuthResponse, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse)
async def signup(user_data: UserCreate, db=Depends(get_database)):
    """Create a new user account."""
    # Check if email already exists
    existing = await db.users.find_one({"email": user_data.email.lower()})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # Create user
    user_doc = {
        "email": user_data.email.lower(),
        "password_hash": hash_password(user_data.password),
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)

    # Generate JWT
    token = create_access_token(user_id, user_doc["email"])

    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            email=user_doc["email"],
            created_at=user_doc["created_at"],
        ),
    )


@router.post("/login", response_model=AuthResponse)
async def login(credentials: UserLogin, db=Depends(get_database)):
    """Authenticate and return JWT."""
    user = await db.users.find_one({"email": credentials.email.lower()})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user_id = str(user["_id"])
    token = create_access_token(user_id, user["email"])

    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            email=user["email"],
            created_at=user["created_at"],
        ),
    )
