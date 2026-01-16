from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.models import User
from app.schemas.user import UserResponse, UserTermUpdate
from app.dependencies import get_current_user, get_db
from app.service.user_service import UserService

router = APIRouter(prefix="/user", tags=["User"])

@router.get("", response_model=UserResponse)
def get_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = UserService(db)
    return service.get_user_info(current_user)

@router.patch("/term", response_model=UserResponse)
def update_terms(
    term_data: UserTermUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = UserService(db)
    return service.update_terms(current_user, term_data.terms)
