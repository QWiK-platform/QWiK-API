from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.deploy import DeployRequest, DeployResponse
from app.service.deploy_service import DeployService
from app.dependencies import get_current_user
from app.models.models import User

router = APIRouter(prefix="/deploy", tags=["Deploy"])

@router.post("/", response_model=DeployResponse)
async def request_deploy(
    request: DeployRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) #  로그인한 유저만 통과
):
    # 서비스 실행
    service = DeployService(db)
    result = await service.create_project_and_deploy(current_user, request)
    return result