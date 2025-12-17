from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 데이터베이스 주소
# DATABASE_URL = "postgresql://user:password@localhost:5432/qwik_db"
DATABASE_URL = settings.DATABASE_URL

# 엔진 시동 (데이터베이스와 연결)
engine = create_engine(DATABASE_URL)

# 작업자(세션) 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 세션을 빌려주는 함수 (FastAPI가 쓸 도구)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()