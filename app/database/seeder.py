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

def init_mock_data(db: Session):
    """
    개발용 더미 데이터 생성 (유저, 프로젝트, 배포 이력 등)
    """
    # 1. 테스트 유저 확인 (없으면 생성)
    test_user = db.query(User).filter(User.username == "ta3wook").first()
    if not test_user:
        print("🌱 테스트 유저(ta3wook) 생성 중...")
        test_user = User(
            username="ta3wook",
            email="ta3wook@example.com",
            github_id="ta3wook_gh",
            plan_id=1  # STARTER
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

    # 2. 프로젝트 데이터 확인 (이미 있으면 스킵)
    if db.query(Project).filter(Project.user_id == test_user.user_id).first():
        return

    print("🌱 프로젝트 및 배포 더미 데이터 생성 중...")

    # 더미 프로젝트 리스트
    projects_data = [
        {
            "repo_name": "QWiK-FE",
            "repo_url": "https://github.com/ta3wook/QWiK-FE",
            "domain": "qwik-fe.qwik.com",
            "status": True,
            "s3_path": f"projects/{test_user.user_id}/QWiK-FE",
            "storage_used": 240,
            "traffic_used": 1200,
            "commit_message": "feat: changed layout"
        },
        {
            "repo_name": "QWiK-API",
            "repo_url": "https://github.com/ta3wook/QWiK-API",
            "domain": "qwik-api.qwik.com",
            "status": True,
            "s3_path": f"projects/{test_user.user_id}/QWiK-API",
            "storage_used": 512,
            "traffic_used": 2400,
            "commit_message": "fix: database connection pool optimization"
        },
        {
            "repo_name": "blog-engine",
            "repo_url": "https://github.com/ta3wook/blog-engine",
            "domain": "blog.qwik.com",
            "status": False, # 중지된 프로젝트
            "s3_path": f"projects/{test_user.user_id}/blog-engine",
            "storage_used": 64,
            "traffic_used": 400,
            "commit_message": "feat: add markdown editor"
        }
    ]

    for p_data in projects_data:
        # 프로젝트 생성
        project = Project(
            user_id=test_user.user_id,
            repo_name=p_data["repo_name"],
            repo_url=p_data["repo_url"],
            domain=p_data["domain"],
            status=p_data["status"],
            s3_path=p_data["s3_path"],
            reload_at=datetime.now() if p_data["status"] else None
        )
        db.add(project)
        db.flush() # project_id 생성을 위해 flush

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

        # (옵션) 이전 배포 이력 추가 (정렬 테스트용)
        old_deployment = Deployment(
            project_id=project.project_id,
            status=DeploymentStatus.FAILED,
            commit_hash="e5f6g7h",
            commit_message="chore: initial commit",
            created_at=datetime.now() - timedelta(days=1)
        )
        db.add(old_deployment)

    db.commit()
    print("더미 데이터 생성 완료!")