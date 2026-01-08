from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

import boto3

from app.database.database import engine, SessionLocal
from app.models import models
from app.routers import auth, deploy, user, dashboard

from app.database.seeder import init_plans

from app.core.config import settings

# DB 테이블 생성
models.Base.metadata.create_all(bind=engine)

# DB에 기본 요금제 저장
def init_db():
    db = SessionLocal()
    try:
        init_plans(db)
    finally:
        db.close()

# 서버 켤 때 실행
init_db()

app = FastAPI()

# 세션 설정 (Authlib 사용 시 필요함)
app.add_middleware(
    SessionMiddleware, 
    secret_key=settings.SECRET_KEY,
    same_site="lax",      #  외부 사이트(GitHub)에서 돌아올 때 쿠키 허용 (개발용)
    https_only=False      #  http://localhost 에서도 쿠키 허용 (개발용)
)

# CORS 설정 (개발 환경)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://qw1k.cloud",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # 허용할 출처 목록
    allow_origin_regex="https?://.*", # 모든 도메인/프로토콜 허용 (CORS 에러 방지)
    allow_credentials=True,     # 쿠키/인증정보 포함 허용
    allow_methods=["*"],        # 모든 HTTP 메서드 허용 (GET, POST...)
    allow_headers=["*"],        # 모든 헤더 허용
)

# 라우터 등록
app.include_router(auth.router)
app.include_router(deploy.router)
app.include_router(user.router)
app.include_router(dashboard.router)

# Root
@app.get("/")
def read_root():
    return {"message": "QWiK Server Running"}