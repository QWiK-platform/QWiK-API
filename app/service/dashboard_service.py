from uuid import UUID
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.models import Project, Deployment, User, Usage, Plan, DeploymentStatus
from app.schemas.dashboard import (
    ProjectDetailResponse, DeploymentHistoryDTO, 
    AllHistoryResponse, GlobalDeploymentHistoryDTO
)


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_history(self, user: User) -> AllHistoryResponse:
        # User가 소유한 모든 프로젝트의 배포 이력 조회 (최신순 10개, Success/Failed만)
        results = (
            self.db.query(Deployment, Project.repo_name)
            .join(Project, Deployment.project_id == Project.project_id)
            .filter(
                Project.user_id == user.user_id,
                Deployment.status.in_([DeploymentStatus.SUCCESS, DeploymentStatus.FAILED])
            )
            .order_by(desc(Deployment.created_at))
            .limit(10)
            .all()
        )

        history_list = []
        for deployment, repo_name in results:
            history_list.append(
                GlobalDeploymentHistoryDTO(
                    deployment_id=deployment.deployment_id,
                    project_id=deployment.project_id,
                    repo_name=repo_name,
                    status=deployment.status.value.lower(),
                    commit_message=deployment.commit_message,
                    created_at=deployment.created_at
                )
            )

        return AllHistoryResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            history=history_list
        )

    def get_project_detail(self, project_id: UUID, user_id: UUID) -> ProjectDetailResponse:
        # 1. 프로젝트 조회 (User, Usage, Plan 정보 함께 로딩하도록 쿼리 최적화 가능하지만, 여기서는 ORM 관계 활용)
        project = self.db.query(Project).filter(Project.project_id == project_id).first()

        # 2. 프로젝트 존재 확인
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # 3. 권한 확인 (본인 프로젝트인지)
        if project.user_id != user_id:
            raise HTTPException(status_code=403, detail="Permission denied")

        # 4. 배포 이력 조회 (최신순 10개, 완료된 상태만)
        # Relationship을 이용해도 되지만, limit 처리를 위해 별도 쿼리가 효율적일 수 있음
        # 하지만 ORM lazy loading을 활용해서 Python 레벨에서 처리하거나,
        # 쿼리로 명시적으로 가져올 수 있음. 여기서는 명확하게 쿼리 작성.
        deployments = (
            self.db.query(Deployment)
            .filter(
                Deployment.project_id == project_id,
                Deployment.status.in_([DeploymentStatus.SUCCESS, DeploymentStatus.FAILED])
            )
            .order_by(desc(Deployment.created_at))
            .limit(10)
            .all()
        )

        history_dtos = []
        for d in deployments:
            history_dtos.append(
                DeploymentHistoryDTO(
                    build_status=d.status.value.lower(), # 소문자로 변환 (e.g., "Failed" -> "failed")
                    commit_message=d.commit_message,
                    created_at=d.created_at
                )
            )

        # 5. 상태값 변환
        status_str = "active" if project.status else "inactive"

        # 6. Usage 정보 (Bytes -> MB 변환)
        storage_used = 0
        traffic_used = 0
        if project.usage:
            # 1 MB = 1024 * 1024 Bytes
            storage_used = project.usage.storage_used // (1024 * 1024)
            traffic_used = project.usage.traffic_used // (1024 * 1024)
        
        # 7. Plan ID 조회 (User를 통해)
        # user는 relationship으로 로딩됨
        plan_id = project.user.plan_id if project.user else 1 # Default fallback

        # 8. Domain 가공
        domain_str = project.domain
        if domain_str and domain_str.endswith(".qwik.com"):
            domain_str = domain_str[:-9]  # Remove last 9 characters (.qwik.com)

        # 9. Response 생성
        latest_deployment_id = deployments[0].deployment_id if deployments else None

        return ProjectDetailResponse(
            project_id=project.project_id,
            deployment_id=latest_deployment_id,
            username=project.user.username if project.user else "",
            plan_id=plan_id,
            repo_name=project.repo_name,
            domain=domain_str,
            storage_used=storage_used,
            traffic_used=traffic_used,
            status=status_str,
            status_changed_at=project.status_changed_at,
            history=history_dtos
        )
