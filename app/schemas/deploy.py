from pydantic import BaseModel, HttpUrl, field_validator

class DeployRequest(BaseModel):
    repo_url: HttpUrl # "https://..." 형식이 아니면 에러 발생
    
    @field_validator('repo_url', mode='after')
    @classmethod
    def validate_github_url(cls, v: HttpUrl) -> HttpUrl:
        """Ensure github_url.path is a valid string"""
        if not v.path:
            raise ValueError("GitHub URL must have a valid path")
        return v

class DeployResponse(BaseModel):
    project_id: str
    repo_url: HttpUrl

class SQSPayload(BaseModel):
    repo_url: str
    user_id: str
    deployment_id: str