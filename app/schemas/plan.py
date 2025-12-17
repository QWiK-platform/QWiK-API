from pydantic import BaseModel

# Base Model
class PlanBase(BaseModel):
    name: str
    price: int
    storage: int
    traffic: int
    projects: int

# [응답용] DB에서 꺼내서 보여줄 때 (ID 포함)
class PlanResponse(PlanBase):
    plan_id: int

    class Config:
        from_attributes = True # DB 객체를 Pydantic으로 자동 변환