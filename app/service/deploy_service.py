# app/service/deploy_service.py
import boto3
import httpx
import json
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import models
from app.schemas.deploy import DeployRequest
from app.core.config import settings

class DeployService:
    def __init__(self, db: Session):
        self.db = db
        self.sqs = boto3.client("sqs", region_name=settings.AWS_REGION)
        self.queue_url = settings.SQS_QUEUE_URL

    async def create_project_and_deploy(self, user: models.User, request_data: DeployRequest):
        # 1. [검사] 요금제 한도 확인 (프로젝트 개수)
        # 내 프로젝트 개수 vs 요금제 허용 개수 비교
        if len(user.projects_rel) >= user.plan.projects:
            raise HTTPException(status_code=400, detail="요금제의 프로젝트 생성 한도를 초과했습니다.")

        # 2. [검사] GitHub 주소 파싱 (주소에서 owner랑 repo 이름만 발라내기)
        # 예: https://github.com/taewook/my-app -> taewook, my-app
        try:
            path_parts = (request_data.repo_url.path or "").strip("/").split("/")
            owner, repo_name = path_parts[-2], path_parts[-1]
        except:
            raise HTTPException(status_code=400, detail="잘못된 GitHub URL입니다.")

        # 3. [검사] GitHub API로 진짜 존재하는지 & 사이즈 확인
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://api.github.com/repos/{owner}/{repo_name}")
            if resp.status_code != 200:
                raise HTTPException(status_code=404, detail="GitHub 리포지토리를 찾을 수 없습니다 (혹은 비공개입니다).")
            
            repo_info = resp.json()
            repo_size_kb = repo_info.get("size", 0) # KB 단위
            repo_size_bytes = repo_size_kb * 1024

            # 4. [검사] 용량 체크 (요금제 스토리지 vs 리포지토리 크기)
            if repo_size_bytes > user.plan.storage:
                raise HTTPException(status_code=400, detail="리포지토리 용량이 요금제 한도를 초과합니다.")

        # 5. [등록] 모든 검사 통과 DB에 저장 (Active 상태)
        
        # 5-1. 프로젝트 생성
        new_project = models.Project(
            user_id=user.user_id,
            repo_url=str(request_data.repo_url),
            repo_name=repo_name,
            domain=f"{repo_name}.qwik.app", # 임시 도메인 생성
            status=models.ProjectStatus.ACTIVE
        )
        self.db.add(new_project)
        self.db.flush() # ID를 미리 받기 위해 flush

        # 5-2. 배포 기록 생성
        new_deployment = models.Deployment(
            project_id=new_project.project_id,
            status=models.DeploymentStatus.QUEUED,
            commit_hash="latest", # 실제로는 깃허브에서 가져와야 함 (지금은 임시)
            commit_message="First deployment"
        )
        self.db.add(new_deployment)
        
        # 5-3. 사용량(Usage) 테이블 초기화
        new_usage = models.Usage(project_id=new_project.project_id)
        self.db.add(new_usage)

        self.db.commit()

        sqs_payload = {
            "repo_url": str(request_data.repo_url),  # 요청에서 받음
            "user_id": str(user.user_id),  # DB/토큰에서 받음
            "deployment_id": str(new_deployment.deployment_id)  # 방금 DB에 저장하고 받은 ID
        }

        try:
            self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(sqs_payload)
            )

            # SQS 전송 성공 시 상태 업데이트
            new_deployment.status = models.DeploymentStatus.QUEUED
            self.db.commit()

            return {"projectId": 1, "repo_url": "https://test.qw1k.cloud"}

        except Exception as e:
            # SQS 전송 실패 시 롤백하거나 상태를 FAILED로 변경
            self.db.rollback()
            raise HTTPException(status_code=500, detail="배포 요청 실패")