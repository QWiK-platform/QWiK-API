from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    SECRET_KEY: str
    DATABASE_URL: str

    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_REDIRECT_URI: str

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 6000 # 100 hours

    # AWS 리전: 보통 고정해서 쓰므로 기본값 지정 (필요 시 .env로 덮어쓰기 가능)
    AWS_REGION: str = "ap-northeast-2"

    # SQS 대기열 URL: 배포 환경마다 다르므로 필수값으로 설정
    SQS_QUEUE_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

settings = Settings()