from pydantic import BaseModel, HttpUrl, field_validator


class DeployRequest(BaseModel):
    repo_url: HttpUrl  # "https://..." 형식이 아니면 에러 발생

    @field_validator('repo_url', mode='after')
    @classmethod
    def validate_github_url(cls, v: HttpUrl) -> HttpUrl:
        """GitHub URL의 path가 유효한지 확인 (owner/repo 형식)"""
        if not v.path or len(v.path.strip("/").split("/")) < 2:
            raise ValueError("GitHub URL must have a valid path (e.g., /owner/repo)")
        return v


class DeployResponse(BaseModel):
    project_id: str  # UUID를 문자열로 반환
    deployment_id: str  # UUID를 문자열로 반환
    repo_url: HttpUrl


class SQSPayload(BaseModel):
    repo_url: str
    user_id: str  # UUID를 문자열로
    deployment_id: str  # UUID를 문자열로
