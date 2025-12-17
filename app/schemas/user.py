from pydantic import BaseModel, UUID4
from typing import Optional
from app.schemas.plan import PlanResponse # 방금 만든 플랜 양식 가져오기

class UserResponse(BaseModel):
    user_id: UUID4
    username: str
    email: str
    github_id: str
    
    # DB의 user.plan 객체를 PlanResponse 양식에 맞춰 보여줌
    plan: PlanResponse 

    class Config:
        from_attributes = True