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