from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.models import User, Project
from app.dependencies import get_current_user, get_db
from app.schemas.dashboard import DashboardResponse, ProjectDTO, UsageDTO, ProjectDetailResponse
from app.service.dashboard_service import DashboardService


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project_detail(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = DashboardService(db)
    return service.get_project_detail(project_id, current_user.user_id)


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. 현재 사용자의 프로젝트 목록 조회
    projects = db.query(Project).filter(Project.user_id == current_user.user_id).all()
    
    project_dtos = []
    for project in projects:
        # 2. 각 프로젝트의 최신 배포 이력 찾기
        latest_commit_message = None
        latest_reload_at = None
        
        if project.deployments:
            # created_at 기준 내림차순 정렬하여 가장 최신 것 하나 가져오기
            # (Python 리스트 정렬 사용)
            sorted_deployments = sorted(project.deployments, key=lambda d: d.created_at, reverse=True)
            latest = sorted_deployments[0]
            latest_commit_message = latest.commit_message
            latest_reload_at = latest.created_at
        
        # 3. 사용량 정보 매핑
        usage_dto = None
        if project.usage:
            usage_dto = UsageDTO.model_validate(project.usage)

        # 4. DTO 생성
        project_dto = ProjectDTO(
            project_id=project.project_id,
            username=current_user.username,
            usage=usage_dto,
            repo_name=project.repo_name,
            domain=project.domain,
            status=project.status,
            created_at=project.created_at,
            commit_message=latest_commit_message,
            reload_at=latest_reload_at
        )
        project_dtos.append(project_dto)
        
    return DashboardResponse(projects=project_dtos)