# backend/app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.services.user_service import UserService
from app.domain.schemas.user import UserCreate, User, UserWithToken
from app.domain.schemas.token import Token
from app.core.exceptions import AuthenticationError, ValidationError

router = APIRouter()
user_service = UserService()

@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db), 
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Token:
    """
    Get an access token for future requests using OAuth2 compatible form.
    """
    try:
        user_with_token = user_service.authenticate(
            db, email=form_data.username, password=form_data.password
        )
        return Token(
            access_token=user_with_token.access_token,
            token_type=user_with_token.token_type
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e.detail),
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/register", response_model=User)
def register(*, db: Session = Depends(get_db), user_in: UserCreate) -> User:
    """
    Create a new user.
    """
    try:
        user = user_service.create_user(db, obj_in=user_in)
        return user
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail),
        )

@router.get("/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current user information.
    """
    return current_user