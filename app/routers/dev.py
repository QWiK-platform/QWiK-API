from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.seeder import create_sample_projects_for_user
from app.dependencies import get_current_user
from app.models.models import User

router = APIRouter(prefix="/dev", tags=["dev"])


@router.post("/seed-sample")
def seed_sample_project(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    현재 로그인한 사용자에게 샘플 프로젝트를 생성합니다.
    (개발/테스트 환경용)
    """
    created = create_sample_projects_for_user(db, current_user)

    if created:
        return {"message": "샘플 프로젝트 생성 완료"}
    else:
        return {"message": "이미 프로젝트가 존재합니다"}
