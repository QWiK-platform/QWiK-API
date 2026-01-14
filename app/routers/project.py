from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.service.project_service import ProjectService
from app.dependencies import get_current_user
from app.models.models import User
from app.schemas.project import DomainChangeRequest, DomainChangeResponse

router = APIRouter(prefix="/projects", tags=["Project"])


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
    service = ProjectService(db)
    await service.delete_project(current_user, project_id)
    return Response(status_code=204)


@router.patch("/{project_id}/domain", response_model=DomainChangeResponse)
async def change_domain(
    project_id: str,
    request: DomainChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    프로젝트 도메인을 변경합니다.

    - 서브도메인명만 입력 (예: my-app, moonu)
    - 영문 소문자, 숫자, 하이픈만 허용
    - 하이픈으로 시작하거나 끝날 수 없음
    """
    service = ProjectService(db)
    return await service.change_domain(current_user, project_id, request.new_domain)
