# app/service/deploy_service.py
import boto3
import httpx
import json
import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import models
from app.schemas.deploy import DeployRequest, DeployResponse
from app.core.config import settings
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class DeployService:
    def __init__(self, db: Session):
        self.db = db
        self.sqs = boto3.client("sqs", region_name=settings.AWS_REGION)
        self.s3 = boto3.client("s3", region_name=settings.AWS_REGION)
        self.queue_url = settings.SQS_QUEUE_URL

    async def create_project_and_deploy(self, user: models.User, request_data: DeployRequest):
        logger.info(f"Deploy request received - User: {user.username}, Repo: {request_data.repo_url}")
        # 1. [검사] GitHub 주소 파싱 (주소에서 owner랑 repo 이름만 발라내기)
        # 예: https://github.com/taewook/my-app -> taewook, my-app
        try:
            path = (request_data.repo_url.path or "").strip("/")
            if path.endswith(".git"):
                path = path[:-4]
            path_parts = path.split("/")
            owner, repo_name = path_parts[-2], path_parts[-1]
        except Exception as e:
            logger.error(f"Invalid GitHub URL format: {request_data.repo_url} - Error: {e}")
            raise HTTPException(status_code=400, detail="잘못된 GitHub URL입니다.")

        # 2. [검사] 이미 존재하는 프로젝트인지 확인
        existing_project = self.db.query(models.Project).filter(
            models.Project.user_id == user.user_id,
            models.Project.repo_name == repo_name
        ).first()

        # 3. [검사] 요금제 한도 확인 (새 프로젝트인 경우에만)
        if not user.plan:
            logger.error(f"User {user.username} has no plan assigned.")
            raise HTTPException(status_code=500, detail="사용자의 요금제 정보가 설정되지 않았습니다.")

        if not existing_project:
            if len(user.projects_rel) >= user.plan.projects:
                logger.warning(f"Project limit exceeded for user {user.username}")
                raise HTTPException(status_code=400, detail="요금제의 프로젝트 생성 한도를 초과했습니다.")

        # 4. [검사] GitHub API로 진짜 존재하는지 & 사이즈 확인
        async with httpx.AsyncClient() as client:
            # TODO: GitHub API 호출 시 Rate Limit 제한을 피하기 위해 사용자 토큰을 헤더에 추가해야 함
            headers = {}
            # User 모델에 저장된 토큰 필드명에 맞춰 가져옵니다 (access_token 또는 github_token)
            token = getattr(user, "access_token", None) or getattr(user, "github_token", None)
            if token:
                headers["Authorization"] = f"Bearer {token}"

            logger.info(f"Verifying GitHub repository: {owner}/{repo_name}")
            resp = await client.get(f"https://api.github.com/repos/{owner}/{repo_name}", headers=headers)
            if resp.status_code != 200:
                logger.error(f"GitHub repo not found or inaccessible. Status: {resp.status_code}")
                raise HTTPException(status_code=404, detail="GitHub 리포지토리를 찾을 수 없습니다 (혹은 비공개입니다).")
            
            repo_info = resp.json()
            repo_size_kb = repo_info.get("size", 0) # KB 단위
            repo_size_bytes = repo_size_kb * 1024

            # 4. [검사] 용량 체크 (요금제 스토리지 vs 리포지토리 크기)
            if repo_size_bytes > user.plan.storage:
                logger.warning(f"Storage limit exceeded. Repo: {repo_size_bytes} bytes, Limit: {user.plan.storage}")
                raise HTTPException(status_code=400, detail="리포지토리 용량이 요금제 한도를 초과합니다.")
            
            # 4-1. Github 최신 커밋 해시 및 메시지 가져오기
            default_branch = repo_info.get("default_branch", "main")
            commit_resp = await client.get(f"https://api.github.com/repos/{owner}/{repo_name}/commits/{default_branch}", headers=headers)
            
            last_commit_hash = "latest"
            last_commit_message = "First deployment"
            if commit_resp.status_code == 200:
                commit_data = commit_resp.json()
                last_commit_hash = commit_data.get("sha", "latest")
                last_commit_message = commit_data.get("commit", {}).get("message", "First deployment")

        # 5. [등록] 모든 검사 통과 DB에 저장 (Active 상태)
        
        if existing_project:
            project_id = existing_project.project_id
            existing_project.reload_at = datetime.now()
        else:
            # 5-1. 프로젝트 생성
            new_project = models.Project(
                user_id=user.user_id,
                repo_url=str(request_data.repo_url),
                repo_name=repo_name,
                domain=None, # 워커가 배포 완료 후 업데이트할 거라 초기는 None
                status=True,
                created_at=datetime.now()
            )
            self.db.add(new_project)
            self.db.flush() # ID를 미리 받기 위해 flush
            project_id = new_project.project_id

            # 5-3. 사용량(Usage) 테이블 초기화 (새 프로젝트일 때만)
            new_usage = models.Usage(project_id=project_id)
            self.db.add(new_usage)
            self.db.flush()

        # 5-2. 배포 기록 생성
        deployment = None
        if existing_project:
            deployment = self.db.query(models.Deployment).filter(
                models.Deployment.project_id == project_id
            ).order_by(models.Deployment.deployment_id.desc()).first()

        if deployment:
            deployment.status = models.DeploymentStatus.QUEUED
            deployment.commit_hash = last_commit_hash
            deployment.commit_message = last_commit_message
        else:
            deployment = models.Deployment(
                project_id=project_id,
                status=models.DeploymentStatus.QUEUED,
                commit_hash=last_commit_hash,
                commit_message=last_commit_message
            )
            self.db.add(deployment)
        self.db.flush() # deployment_id 생성을 위해 flush

        sqs_payload = {
            "repo_url": str(request_data.repo_url),  # 요청에서 받음
            "user_id": str(user.user_id),  # DB/토큰에서 받음
            "username": user.username,
            "deployment_id": str(deployment.deployment_id)  # 방금 DB에 저장하고 받은 ID
        }

        try:
            logger.info(f"Sending deployment message to SQS. Deployment ID: {deployment.deployment_id}")
            self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(sqs_payload)
            )

            # SQS 전송 성공 시 DB commit
            # 62번 줄에서 QUEUED로 추가하므로 여기서는 성공 시 db commit 하도록
            self.db.commit()
            logger.info(f"Deployment successfully queued. Project ID: {project_id}")

            return DeployResponse(
                project_id=str(project_id),
                repo_url=request_data.repo_url
            )

        except Exception as e:
            # SQS 전송 실패 시 롤백하거나 상태를 FAILED로 변경
            logger.error(f"Failed to queue deployment: {e}", exc_info=True)
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"배포 요청 실패: {e}")

    async def delete_project(self, user: models.User, project_id: str):
        logger.info(f"Delete project request - User: {user.username}, Project ID: {project_id}")

        # 1. 프로젝트 조회
        project = self.db.query(models.Project).filter(
            models.Project.project_id == project_id
        ).first()

        if not project:
            logger.error(f"Project not found: {project_id}")
            raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")

        # 2. 권한 확인
        if project.user_id != user.user_id:
            logger.error(f"Permission denied for user {user.username} on project {project_id}")
            raise HTTPException(status_code=403, detail="해당 프로젝트에 대한 권한이 없습니다.")

        # 3. 최신 배포 상태 확인 (SUCCESS일 때만 삭제 가능)
        latest_deployment = self.db.query(models.Deployment).filter(
            models.Deployment.project_id == project_id
        ).order_by(models.Deployment.created_at.desc()).first()

        if not latest_deployment or latest_deployment.status != models.DeploymentStatus.SUCCESS:
            logger.warning(f"Cannot delete project {project_id}: deployment status is not SUCCESS")
            raise HTTPException(
                status_code=400,
                detail="배포가 완료된 프로젝트만 삭제할 수 있습니다."
            )

        # 4. S3에서 배포 파일 삭제
        if project.s3_path:
            try:
                self._delete_s3_objects(project.s3_path)
                logger.info(f"S3 objects deleted for project {project_id}")
            except Exception as e:
                logger.error(f"Failed to delete S3 objects: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="리소스 삭제 중 오류가 발생했습니다.")

        # 5. DB에서 프로젝트 삭제 (cascade로 Usage, Deployment, Log 자동 삭제)
        try:
            self.db.delete(project)
            self.db.commit()
            logger.info(f"Project {project_id} deleted successfully")
        except Exception as e:
            logger.error(f"Failed to delete project from DB: {e}", exc_info=True)
            self.db.rollback()
            raise HTTPException(status_code=500, detail="프로젝트 삭제 중 오류가 발생했습니다.")

    def _delete_s3_objects(self, s3_path: str):
        """S3 경로 아래의 모든 객체를 삭제합니다.

        s3_path 형식: users/{USER_ID}/{DEPLOYMENT_ID}
        """
        bucket = settings.S3_BUCKET_NAME

        # prefix 아래의 모든 객체 나열 및 삭제
        paginator = self.s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket, Prefix=s3_path)

        for page in pages:
            if "Contents" not in page:
                continue

            objects_to_delete = [{"Key": obj["Key"]} for obj in page["Contents"]]
            if objects_to_delete:
                self.s3.delete_objects(
                    Bucket=bucket,
                    Delete={"Objects": objects_to_delete}
                )