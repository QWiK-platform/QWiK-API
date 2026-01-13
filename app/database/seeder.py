# app/database/seeder.py
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.models import User, Project, Usage, Deployment, DeploymentStatus, Plan
from app.models import models

INITIAL_PLANS = [
    {
        "plan_id": 1,
        "name": "STARTER",
        "price": 0,
        "projects": 3,
        # 3000MB -> Bytes 변환
        "traffic": 3000 * 1024 * 1024, 
        # 200MB -> Bytes 변환 (projectCapacity를 storage로 매핑)
        "storage": 200 * 1024 * 1024 
    },
    {
        "plan_id": 2,
        "name": "BASIC",
        "price": 4400,
        "projects": 7,
        "traffic": 20000 * 1024 * 1024,
        "storage": 500 * 1024 * 1024
    },
    {
        "plan_id": 3,
        "name": "PRO",
        "price": 7700,
        "projects": 15,
        "traffic": 50000 * 1024 * 1024, # 기본 제공량만 반영
        "storage": 500 * 1024 * 1024
    }
]

def init_plans(db: Session):
    # 이미 데이터가 있으면 아무것도 안 함
    if db.query(models.Plan).filter(models.Plan.plan_id == 1).first():
        return

    print("🌱 초기 요금제 데이터를 심는 중입니다...")
    
    for plan_data in INITIAL_PLANS:
        # 모델 객체 생성
        new_plan = models.Plan(
            plan_id=plan_data["plan_id"],
            name=plan_data["name"],
            price=plan_data["price"],
            projects=plan_data["projects"],
            traffic=plan_data["traffic"],
            storage=plan_data["storage"]
        )
        db.add(new_plan)
    
    db.commit()
    print("요금제 데이터 생성 완료!")


def create_sample_projects_for_user(db: Session, user: User):
    """
    로그인한 사용자에게 샘플 프로젝트 붙여주도록 하는 함수
    """
    # 이미 프로젝트가 있으면 스킵
    if db.query(Project).filter(Project.user_id == user.user_id).first():
        return False

    print(f"🌱 [{user.username}] 샘플 프로젝트 생성 중...")

    # 샘플 프로젝트 리스트
    projects_data = [
        {
            "repo_name": "sample-frontend",
            "repo_url": f"https://github.com/{user.username}/sample-frontend",
            "domain": f"{user.username}-fe.qwik.com",
            "status": True,
            "storage_used": 240,
            "traffic_used": 1200,
            "commit_message": "feat: initial project setup"
        },
    ]

    for p_data in projects_data:
        # 프로젝트 생성 (s3_path는 deployment 생성 후 업데이트)
        project = Project(
            user_id=user.user_id,
            repo_name=p_data["repo_name"],
            repo_url=p_data["repo_url"],
            domain=p_data["domain"],
            status=p_data["status"],
            s3_path=None,
            reload_at=datetime.now() if p_data["status"] else None
        )
        db.add(project)
        db.flush()

        # 사용량(Usage) 생성
        usage = Usage(
            project_id=project.project_id,
            storage_used=p_data["storage_used"],
            traffic_used=p_data["traffic_used"]
        )
        db.add(usage)

        # 배포 이력(Deployment) 생성 (최신 성공 배포 1건)
        deployment = Deployment(
            project_id=project.project_id,
            status=DeploymentStatus.SUCCESS,
            commit_hash="a1b2c3d",
            commit_message=p_data["commit_message"],
            created_at=datetime.now()
        )
        db.add(deployment)
        db.flush()

        # s3_path 업데이트
        project.s3_path = f"/users/{user.user_id}/{deployment.deployment_id}"

        # 이전 배포 이력 추가 (정렬 테스트용)
        old_deployment = Deployment(
            project_id=project.project_id,
            status=DeploymentStatus.FAILED,
            commit_hash="e5f6g7h",
            commit_message="chore: initial commit",
            created_at=datetime.now() - timedelta(days=1)
        )
        db.add(old_deployment)

    db.commit()
    print(f"✅ [{user.username}] 샘플 프로젝트 생성 완료!")
    return True