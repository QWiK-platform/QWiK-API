from pydantic import BaseModel
from typing import Optional

class GitHubLoginRequest(BaseModel):
    code: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_name: Optional[str] = None