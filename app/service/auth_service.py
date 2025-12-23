from sqlalchemy.orm import Session
from app.models.models import User
from app.database.seeder import create_sample_projects_for_user

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_user(self, user_info: dict):
        # GitHub는 id를 숫자로 주기 때문에 문자열로 바꿔서 저장합니다.
        # user_info 딕셔너리 구조는 Authlib 버전에 따라 다를 수 있어 안전하게 .get() 사용
        github_id = str(user_info.get('id'))

        # 1. 이미 가입한 회원인지 확인
        existing_user = self.db.query(User).filter(User.github_id == github_id).first() # 없으면 None, 있으면 해당 User 객체가 저장됨
        if existing_user:
            return existing_user

        # 2. 처음 온 사람이면 회원가입 (DB 저장)
        new_user = User(
            github_id=github_id,
            username=user_info.get('login'),
            email=user_info.get('email') or f"{user_info.get('login')}@no-email.com",
            plan_id=1 # 기본 플랜 ID, 추후 변경
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)

        # 3. 개발 환경에서 샘플 프로젝트 자동 생성
        create_sample_projects_for_user(self.db, new_user)

        return new_user