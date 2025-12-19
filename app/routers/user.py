from fastapi import APIRouter, Depends
from app.models.models import User
from app.schemas.user import UserResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/user", tags=["User"])

@router.get("/", response_model=UserResponse)
async def get_user_info(current_user: User = Depends(get_current_user)):

    return current_user
