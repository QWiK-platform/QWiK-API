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


class DeploymentHistoryDTO(BaseModel):
    deployment_id: UUID
    build_status: str
    commit_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailResponse(BaseModel):
    project_id: UUID
    username: str
    plan_id: int
    repo_name: str
    domain: Optional[str]
    storage_used: int
    traffic_used: int
    status: str
    status_changed_at: datetime
    history: List[DeploymentHistoryDTO]

    model_config = ConfigDict(from_attributes=True)


class GlobalDeploymentHistoryDTO(BaseModel):
    deployment_id: UUID
    project_id: UUID
    repo_name: str
    status: str
    commit_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AllHistoryResponse(BaseModel):
    user_id: UUID
    username: str
    email: str
    history: List[GlobalDeploymentHistoryDTO]

    model_config = ConfigDict(from_attributes=True)