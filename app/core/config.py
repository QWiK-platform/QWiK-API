import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # JWT 암호화에 사용할 시크릿키
    SECRET_KEY: str =  os.getenv("SECRET_KEY")
    # 암호화 알고리즘
    ALGORITHM: str = "HS256"
    # 토큰 유효 기간 (분 단위)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL: str = os.getenv("DATABASE_URL")

    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID") 
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET")
    GITHUB_REDIRECT_URI: str = os.getenv("GITHUB_REDIRECT_URI")

settings = Settings()