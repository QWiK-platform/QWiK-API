from pydantic import BaseModel, HttpUrl, field_validator

# [요청] 사용자가 보낼 데이터
class DeployRequest(BaseModel):
    github_url: HttpUrl # "https://..." 형식이 아니면 에러 발생
    
    @field_validator('github_url', mode='after')
    @classmethod
    def validate_github_url(cls, v: HttpUrl) -> HttpUrl:
        """Ensure github_url.path is a valid string"""
        if not v.path:
            raise ValueError("GitHub URL must have a valid path")
        return v

# [응답] 성공했을 때 줄 데이터
# class DeployResponse(BaseModel):
#     status: str
#     message: str

class DeployResponse(BaseModel):
    projectId: int
    repo_url: HttpUrl