# app/service/deploy_service.py
import json
import boto3
import httpx
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import models
from app.schemas.deploy import DeployRequest, DeployResponse
from app.core.config import settings


class DeployService:
    def __init__(self, db: Session):
        self.db = db
        self.sqs = boto3.client("sqs", region_name=settings.AWS_REGION)
        self.queue_url = settings.SQS_QUEUE_URL

    async def create_project_and_deploy(self, user: models.User, request_data: DeployRequest) -> DeployResponse:
        # 1. [검사] 요금제 한도 확인 (프로젝트 개수)
        if len(user.projects_rel) >= user.plan.projects:
            raise HTTPException(status_code=400, detail="요금제의 프로젝트 생성 한도를 초과했습니다.")

        # 2. [검사] GitHub 주소 파싱
        # 예: https://github.com/taewook/my-app -> taewook, my-app
        try:
            path_parts = (request_data.repo_url.path or "").strip("/").split("/")
            if len(path_parts) < 2:
                raise ValueError("URL path가 너무 짧습니다")
            owner, repo_name = path_parts[-2], path_parts[-1]
        except (IndexError, ValueError) as e:
            raise HTTPException(status_code=400, detail=f"잘못된 GitHub URL입니다: {e}")

        # 3. [검사] GitHub API로 존재 여부 & 사이즈 확인
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://api.github.com/repos/{owner}/{repo_name}")
            if resp.status_code != 200:
                raise HTTPException(status_code=404, detail="GitHub 리포지토리를 찾을 수 없습니다 (혹은 비공개입니다).")

            repo_info = resp.json()
            repo_size_bytes = repo_info.get("size", 0) * 1024  # KB -> Bytes

            # 4. [검사] 용량 체크 (요금제 스토리지 vs 리포지토리 크기)
            if repo_size_bytes > user.plan.storage:
                raise HTTPException(status_code=400, detail="리포지토리 용량이 요금제 한도를 초과합니다.")

            # GitHub에서 최신 커밋 해시 가져오기
            default_branch = repo_info.get("default_branch", "main")
            commit_resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo_name}/commits/{default_branch}"
            )
            if commit_resp.status_code == 200:
                commit_info = commit_resp.json()
                commit_hash = commit_info.get("sha", "unknown")[:40]
                commit_message = commit_info.get("commit", {}).get("message", "")
            else:
                commit_hash = "unknown"
                commit_message = ""

        # 5. [등록] 모든 검사 통과 -> DB에 저장 (flush만, commit은 SQS 성공 후)

        # 5-1. 프로젝트 생성
        new_project = models.Project(
            user_id=user.user_id,
            repo_url=str(request_data.repo_url),
            repo_name=repo_name,
            domain=f"{repo_name}.qwik.app",
            status=True  # Boolean 타입
        )
        self.db.add(new_project)
        self.db.flush()  # ID를 미리 받기 위해 flush (아직 commit 아님)

        # 5-2. 배포 기록 생성
        new_deployment = models.Deployment(
            project_id=new_project.project_id,
            status=models.DeploymentStatus.QUEUED,
            commit_hash=commit_hash,
            commit_message=commit_message[:500] if commit_message else None  # 너무 긴 메시지 방지
        )
        self.db.add(new_deployment)

        # 5-3. 사용량(Usage) 테이블 초기화
        new_usage = models.Usage(project_id=new_project.project_id)
        self.db.add(new_usage)
        self.db.flush()

        # 6. [SQS] 빌드 서버에 작업 요청
        sqs_payload = {
            "repo_url": str(request_data.repo_url),
            "user_id": str(user.user_id),
            "deployment_id": str(new_deployment.deployment_id)
        }

        try:
            self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(sqs_payload)
            )

            # SQS 전송 성공 시 DB commit
            self.db.commit()

            return DeployResponse(
                project_id=str(new_project.project_id),
                repo_url=request_data.repo_url
            )

        except Exception as e:
            # SQS 전송 실패 시 롤백 (아직 commit 안 했으므로 가능)
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"배포 요청 실패: {e}")
