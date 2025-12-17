from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from app.database.database import get_db
from app.service.auth_service import AuthService

from app.schemas.auth import LoginResponse 
from app.core.security import create_access_token

from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])

# GitHub 등록
oauth = OAuth()
oauth.register(
    name='github',
    client_id=settings.GITHUB_CLIENT_ID,
    client_secret=settings.GITHUB_CLIENT_SECRET,
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
)

@router.get("/login")
async def login(request: Request):
    # GitHub 설정과 일치해야 함 (127.0.0.1)
    redirect_uri = "http://127.0.0.1:8000/auth/callback"
    return await oauth.github.authorize_redirect(request, redirect_uri)

@router.get("/callback", response_model=LoginResponse)
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.github.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail="OAuth Token Error")
        
    user_info = await oauth.github.get('user', token=token)
    profile = user_info.json()

    auth_service = AuthService(db)
    user = auth_service.get_or_create_user(profile)

    # 토큰을 발급
    access_token = create_access_token(data={"sub": str(user.user_id)})

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        # user_name=user.username
    )