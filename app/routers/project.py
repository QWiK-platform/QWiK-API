from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.service.project_service import ProjectService
from app.dependencies import get_current_user
from app.models.models import User

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
