import re
from pydantic import BaseModel, UUID4, HttpUrl, field_validator
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
    status: str            
    
    created_at: datetime
    status_changed_at: datetime

    class Config:
        from_attributes = True


class DomainChangeRequest(BaseModel):
    new_domain: str

    @field_validator("new_domain")
    @classmethod
    def validate_domain_format(cls, v: str) -> str:
        pattern = r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$"
        if not re.match(pattern, v):
            raise ValueError(
                "도메인 형식이 올바르지 않습니다. 영문 소문자, 숫자, 하이픈만 허용되며 하이픈으로 시작하거나 끝날 수 없습니다."
            )
        return v


class DomainChangeResponse(BaseModel):
    project_id: UUID4
    old_domain: str
    new_domain: str