from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.deploy import DeployRequest, DeployResponse
from app.service.deploy_service import DeployService
from app.dependencies import get_current_user
from app.models.models import User

router = APIRouter(prefix="/deploy", tags=["Deploy"])


@router.post("", response_model=DeployResponse, status_code=201)
async def request_deploy(
    request: DeployRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    새 프로젝트를 생성하고 배포를 요청합니다.

    - GitHub 저장소 URL을 받아 검증
    - 프로젝트, 배포 기록, 사용량 테이블 생성
    - SQS에 빌드 작업 요청
    """
    service = DeployService(db)
    return await service.create_project_and_deploy(current_user, request)