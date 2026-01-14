from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class UsageDTO(BaseModel):
    storage_used: int
    traffic_used: int
    
    model_config = ConfigDict(from_attributes=True)

class ProjectDTO(BaseModel):
    project_id: UUID
    username: str
    usage: Optional[UsageDTO] = None
    repo_name: str
    domain: Optional[str] = None
    status: bool
    created_at: datetime
    commit_message: Optional[str] = None
    reload_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class DashboardResponse(BaseModel):
    projects: List[ProjectDTO]