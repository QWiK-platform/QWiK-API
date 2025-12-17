from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.config import settings

# 토큰을 만드는 함수
def create_access_token(data: dict) -> str:
    # 원본 데이터 수정 방지를 위해 복사
    to_encode = data.copy()

    # 만료 시간 설정
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # JWT 표준 Claim이므로 반드시 exp로 작성(소문자)
    to_encode.update({"exp": expire})    

    # JWT로 encode
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt