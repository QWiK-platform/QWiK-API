# app/service/deploy_service.py
import httpx
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import models
from app.schemas.deploy import DeployRequest

class DeployService:
    def __init__(self, db: Session):
        self.db = db

    async def create_project_and_deploy(self, user: models.User, request_data: DeployRequest):
        # 1. [검사] 요금제 한도 확인 (프로젝트 개수)
        # 내 프로젝트 개수 vs 요금제 허용 개수 비교
        if len(user.projects_rel) >= user.plan.projects:
            raise HTTPException(status_code=400, detail="요금제의 프로젝트 생성 한도를 초과했습니다.")

        # 2. [검사] GitHub 주소 파싱 (주소에서 owner랑 repo 이름만 발라내기)
        # 예: https://github.com/taewook/my-app -> taewook, my-app
        try:
            path_parts = (request_data.github_url.path or "").strip("/").split("/")
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
            repo_url=str(request_data.github_url),
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
        
        return {"status": "success", "message": "배포 요청이 접수되었습니다!", "project_id": new_project.project_id}