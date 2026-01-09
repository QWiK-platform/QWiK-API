from fastapi import APIRouter, Depends, Response
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


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    배포된 프로젝트를 삭제합니다.

    - 배포 상태가 SUCCESS인 프로젝트만 삭제 가능
    - S3에서 배포 파일 삭제
    - DB에서 프로젝트 및 관련 레코드 삭제
    """
    service = DeployService(db)
    await service.delete_project(current_user, project_id)
    return Response(status_code=204)