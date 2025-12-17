from pydantic import BaseModel, UUID4, HttpUrl
from datetime import datetime
from typing import Optional

class ProjectCreate(BaseModel):
    repo_url: str          # 깃헙 주소
    repo_name: str         # 레포 이름 (my-app)
    branch: str = "main"   # 브랜치 (기본값 main)

class ProjectResponse(BaseModel):
    project_id: UUID4
    repo_url: str
    repo_name: str
    domain: Optional[str] = None  # 아직 도메인 없을 수도 있음
    status: str            # Active, Inactive
    
    created_at: datetime
    status_changed_at: datetime

    class Config:
        from_attributes = True