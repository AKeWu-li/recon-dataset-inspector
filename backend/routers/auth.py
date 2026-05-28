from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.config import ACCESS_TOKEN_EXPIRE_MINUTES
from backend.database import get_db
from backend.models import User
from backend.schemas import UserCreate, UserResponse, Token
from backend.security import (
    get_password_hash,
    authenticate_user,
    create_access_token
)


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["auth"]
)


@router.post("/register", response_model=UserResponse)
def register_user(
    user_create: UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = (
        db.query(User)
        .filter(User.username == user_create.username)
        .first()
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=400,
            detail="Username already registered."
        )

    user = User(
        username=user_create.username,
        hashed_password=get_password_hash(user_create.password),
        is_active=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=Token)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(
        db,
        form_data.username,
        form_data.password
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }