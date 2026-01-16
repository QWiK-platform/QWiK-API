from pydantic import BaseModel, UUID4, ConfigDict
from datetime import date

class UserTermUpdate(BaseModel):
    terms: date

class UserBase(BaseModel):
    username: str
    email: str

class UserResponse(UserBase):
    user_id: UUID4
    storage_limit: int
    traffic_limit: int
    project_limit: int
    terms: date | None = None  # DB에서 nullable=True이므로

    model_config = ConfigDict(from_attributes=True)
