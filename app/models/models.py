import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Integer, BigInteger, Boolean, DateTime, Text, ForeignKey, Enum, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Relationship, DeclarativeBase, Mapped, mapped_column

# 1. Base Model
class Base(DeclarativeBase):
    pass

# --- Enums (ERD의 Active/Inactive, Status 관리용) ---
class ProjectStatus(str, PyEnum):
    ACTIVE = "Active"
    INACTIVE = "Inactive" # ERD 표기에 맞춤 (Inactive)

class DeploymentStatus(str, PyEnum):
    QUEUED = "Queued"
    BUILDING = "Building"
    SUCCESS = "Success"
    FAILED = "Failed"

# --- Models ---

class Plan(Base):
    __tablename__ = "plans"

    # ERD: plan_id (Key)
    plan_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # ERD: name (요금제 이름)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # ERD: price (금액)
    price: Mapped[int] = mapped_column(Integer, default=0)
    
    # ERD: storage (스토리지 상한선)
    storage: Mapped[int] = mapped_column(BigInteger, default=1073741824) # Byte 단위 권장
    
    # ERD: traffic (트래픽 상한선)
    traffic: Mapped[int] = mapped_column(BigInteger, default=10737418240)
    
    # ERD: projects (프로젝트 개수 상한선)
    projects: Mapped[int] = mapped_column(Integer, default=3)

    # Relationship
    users: Mapped[list["User"]] = Relationship(back_populates="plan")


class User(Base):
    __tablename__ = "users"

    # ERD: user_id (PK, VARCHAR(36) -> UUID로 매핑)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # ERD: plan_id (Key)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.plan_id"), default=1)
    
    # ERD: github_id (UQ)
    github_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    
    # ERD: username
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # ERD: email (UQ)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    
    # ERD: term_version
    term_version: Mapped[str] = mapped_column(String(10), nullable=True)

    # Relationship
    plan: Mapped["Plan"] = Relationship(back_populates="users")
    projects_rel: Mapped[list["Project"]] = Relationship(back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    # ERD: project_id (PK)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # ERD: user_id (FK)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    
    # ERD: repo_url
    repo_url: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # ERD: repo_name
    repo_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # ERD: domain (도메인 주소)
    domain: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    
    # ERD: status (Boolean)
    status: Mapped[bool] = mapped_column(Boolean, default=True)

    # ERD: s3 경로
    s3_path: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # ERD: created_at
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # ERD: status_changed_at
    status_changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # ERD: 재배포 일시
    reload_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationship
    user: Mapped["User"] = Relationship(back_populates="projects_rel")
    usage: Mapped["Usage"] = Relationship(back_populates="project", uselist=False, cascade="all, delete-orphan")
    deployments: Mapped[list["Deployment"]] = Relationship(back_populates="project", cascade="all, delete-orphan")


class Usage(Base):
    __tablename__ = "usage" # ERD 이름: Usage

    # ERD: project_id (PK) - 1:1 관계
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.project_id"), primary_key=True)
    
    # ERD: storage_used
    storage_used: Mapped[int] = mapped_column(BigInteger, default=0)
    
    # ERD: traffic_used
    traffic_used: Mapped[int] = mapped_column(BigInteger, default=0)
    
    # ERD: usage_cycle_start
    usage_cycle_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    project: Mapped["Project"] = Relationship(back_populates="usage")


class Deployment(Base):
    __tablename__ = "deployments"

    # ERD: deployment_id (Key)
    deployment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # ERD: project_id (Key)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.project_id"), nullable=False)
    
    # ERD: status (Queued, Building, Success, Failed)
    status: Mapped[DeploymentStatus] = mapped_column(Enum(DeploymentStatus), default=DeploymentStatus.QUEUED)
    
    # ERD: commit_hash
    commit_hash: Mapped[str] = mapped_column(String(40), nullable=False)
    
    # ERD: commit_message
    commit_message: Mapped[str] = mapped_column(Text, nullable=True)
    
    # ERD: created_at
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    project: Mapped["Project"] = Relationship(back_populates="deployments")
    logs_rel: Mapped["Log"] = Relationship(back_populates="deployment", uselist=False, cascade="all, delete-orphan")


class Log(Base):
    __tablename__ = "logs"

    # ERD: log_id (Key)
    log_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # ERD: deployment_id (Key2) - FK
    deployment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("deployments.deployment_id"), unique=True, nullable=False)
    
    # ERD: project_id (프로젝트 id) - FK
    # (참고: 정규화 관점에서는 deployment_id를 통해 알 수 있으나, ERD에 명시되어 있으므로 추가함)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.project_id"), nullable=False)

    # ERD: log
    log: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationship
    deployment: Mapped["Deployment"] = Relationship(back_populates="logs_rel")