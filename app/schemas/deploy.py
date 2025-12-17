from pydantic import BaseModel, HttpUrl

# [요청] 사용자가 보낼 데이터
class DeployRequest(BaseModel):
    github_url: HttpUrl # "https://..." 형식이 아니면 에러 발생

# [응답] 성공했을 때 줄 데이터
class DeployResponse(BaseModel):
    status: str
    message: str