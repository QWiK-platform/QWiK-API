from pydantic import BaseModel

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_name: str