import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.service.auth_service import AuthService

from app.schemas.auth import LoginResponse, GitHubLoginRequest
from app.core.security import create_access_token

from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/github/callback", response_model=LoginResponse)
async def github_login(payload: GitHubLoginRequest, db: Session = Depends(get_db)):
    """
    프론트엔드에서 받은 Code로 GitHub Access Token을 발급받고, 
    사용자 정보를 조회하여 자체 서비스 토큰(JWT)을 발급합니다.
    """
    
    # 1. GitHub에 Access Token 요청 (POST)
    # httpx를 사용하여 GitHub OAuth 서버와 직접 통신
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            json={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": payload.code,
                # 프론트엔드에서 호출한 리다이렉트 URI와 일치해야 함
                "redirect_uri": "https://qw1k.cloud/auth/callback"
            }
        )
        
    token_data = token_response.json()
    
    # GitHub 응답에 에러가 포함된 경우
    if "error" in token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"GitHub Login Error: {token_data.get('error_description')}"
        )
        
    access_token = token_data.get("access_token")

    # 2. 발급받은 토큰으로 GitHub 사용자 정보 조회 (GET)
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }
        )
    
    if user_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch user info from GitHub")

    profile = user_response.json()

    # 3. DB에서 유저 확인 또는 생성 (기존 로직 활용)
    auth_service = AuthService(db)
    user = auth_service.get_or_create_user(profile)

    # 4. 자체 JWT 토큰 발급
    jwt_token = create_access_token(data={"sub": str(user.user_id)})

    return LoginResponse(
        access_token=jwt_token,
        token_type="bearer",
        user_name=user.username
    )