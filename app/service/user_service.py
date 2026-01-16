from datetime import date
from sqlalchemy.orm import Session
from app.models.models import User
from app.schemas.user import UserResponse

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def _to_response(self, user: User) -> UserResponse:
        # Plan 정보 가져오기 (없으면 기본값 0 처리)
        storage_limit = 0
        traffic_limit = 0
        project_limit = 0
        
        if user.plan:
            # Bytes -> MB 변환
            storage_limit = user.plan.storage // (1024 * 1024)
            traffic_limit = user.plan.traffic // (1024 * 1024)
            project_limit = user.plan.projects
        
        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            storage_limit=storage_limit,
            traffic_limit=traffic_limit,
            project_limit=project_limit,
            terms=user.terms
        )

    def get_user_info(self, user: User) -> UserResponse:
        return self._to_response(user)

    def update_terms(self, user: User, terms_date: date) -> UserResponse:
        user.terms = terms_date
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return self._to_response(user)
