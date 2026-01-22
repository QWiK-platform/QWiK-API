# app/service/project_service.py
import boto3
import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import models
from app.core.config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ProjectService:
    def __init__(self, db: Session):
        self.db = db
        self.s3 = boto3.client("s3", region_name=settings.AWS_REGION)
        self.kvs = boto3.client("cloudfront-keyvaluestore", region_name=settings.AWS_REGION)

    async def delete_project(self, user: models.User, project_id: str):
        logger.info(f"Delete project request - User: {user.username}, Project ID: {project_id}")

        # 1. 프로젝트 조회
        project = self.db.query(models.Project).filter(
            models.Project.project_id == project_id
        ).first()

        if not project:
            logger.error(f"Project not found: {project_id}")
            raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")

        # 2. 권한 확인
        if project.user_id != user.user_id:
            logger.error(f"Permission denied for user {user.username} on project {project_id}")
            raise HTTPException(status_code=403, detail="해당 프로젝트에 대한 권한이 없습니다.")

        # 3. 최신 배포 상태 확인 (QUEUED, BUILDING일 때는 삭제 불가)
        latest_deployment = self.db.query(models.Deployment).filter(
            models.Deployment.project_id == project_id
        ).order_by(models.Deployment.created_at.desc()).first()

        if latest_deployment and latest_deployment.status in [
            models.DeploymentStatus.QUEUED,
            models.DeploymentStatus.BUILDING
        ]:
            logger.warning(f"Cannot delete project {project_id}: deployment is in progress")
            raise HTTPException(
                status_code=400,
                detail="배포가 진행 중인 프로젝트는 삭제할 수 없습니다."
            )

        # 4. S3에서 배포 파일 삭제
        if project.s3_path:
            try:
                self._delete_s3_objects(project.s3_path)
                logger.info(f"S3 objects deleted for project {project_id}")
            except Exception as e:
                logger.error(f"Failed to delete S3 objects: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="리소스 삭제 중 오류가 발생했습니다.")

        # 5. KVS에서 도메인 키 삭제
        if project.domain:
            try:
                self._delete_kvs_key(project.domain)
                logger.info(f"KVS key deleted for project {project_id}: {project.domain}")
            except Exception as e:
                logger.error(f"Failed to delete KVS key: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="KVS 키 삭제 중 오류가 발생했습니다.")

        # 6. DB에서 프로젝트 삭제 (cascade로 Usage, Deployment, Log 자동 삭제)
        try:
            self.db.delete(project)
            self.db.commit()
            logger.info(f"Project {project_id} deleted successfully")
        except Exception as e:
            logger.error(f"Failed to delete project from DB: {e}", exc_info=True)
            self.db.rollback()
            raise HTTPException(status_code=500, detail="프로젝트 삭제 중 오류가 발생했습니다.")

    def _delete_s3_objects(self, s3_path: str):
        """
        S3 지정된 경로 모든 객체 삭제
        """
        bucket = settings.S3_BUCKET_NAME

        # prefix 아래의 모든 객체 나열 및 삭제
        paginator = self.s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket, Prefix=s3_path)

        for page in pages:
            if "Contents" not in page:
                continue

            objects_to_delete = [{"Key": obj["Key"]} for obj in page["Contents"]]
            if objects_to_delete:
                self.s3.delete_objects(
                    Bucket=bucket,
                    Delete={"Objects": objects_to_delete}
                )

    def _delete_kvs_key(self, key: str):
        """
        CloudFront KeyValueStore Key 삭제
        """
        kvs_arn = settings.KVS_ARN

        # 현재 ETag 가져오기
        describe_resp = self.kvs.describe_key_value_store(KvsARN=kvs_arn)
        etag = describe_resp["ETag"]

        # 키 삭제
        self.kvs.delete_key(
            KvsARN=kvs_arn,
            Key=key,
            IfMatch=etag
        )

    def _get_kvs_value(self, key: str) -> str:
        """
        CloudFront KeyValueStore에서 Key의 Value 조회
        """
        kvs_arn = settings.KVS_ARN
        response = self.kvs.get_key(KvsARN=kvs_arn, Key=key)
        return response["Value"]

    def _put_kvs_key(self, key: str, value: str):
        """
        CloudFront KeyValueStore에 Key-Value 추가
        """
        kvs_arn = settings.KVS_ARN

        # 현재 ETag 가져오기
        describe_resp = self.kvs.describe_key_value_store(KvsARN=kvs_arn)
        etag = describe_resp["ETag"]

        # 키 추가
        self.kvs.put_key(
            KvsARN=kvs_arn,
            Key=key,
            Value=value,
            IfMatch=etag
        )

    async def change_domain(self, user: models.User, project_id: str, new_domain: str):
        """
        프로젝트 도메인 변경
        """
        logger.info(f"Change domain request - User: {user.username}, Project ID: {project_id}, New Domain: {new_domain}")

        # 1. 프로젝트 조회
        project = self.db.query(models.Project).filter(
            models.Project.project_id == project_id
        ).first()

        if not project:
            logger.error(f"Project not found: {project_id}")
            raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")

        # 2. 권한 확인
        if project.user_id != user.user_id:
            logger.error(f"Permission denied for user {user.username} on project {project_id}")
            raise HTTPException(status_code=403, detail="해당 프로젝트에 대한 권한이 없습니다.")

        # 3. 도메인 중복 확인 (DB)
        existing = self.db.query(models.Project).filter(
            models.Project.domain == new_domain
        ).first()

        if existing:
            logger.warning(f"Domain already exists: {new_domain}")
            raise HTTPException(status_code=409, detail="이미 사용 중인 도메인입니다.")

        old_domain = project.domain

        # 4. KVS 업데이트
        if old_domain:
            try:
                s3_path = self._get_kvs_value(old_domain)
                self._delete_kvs_key(old_domain)
                self._put_kvs_key(new_domain, s3_path)
                logger.info(f"KVS updated: {old_domain} -> {new_domain}")
            except Exception as e:
                logger.error(f"Failed to update KVS: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="KVS 업데이트 중 오류가 발생했습니다.")

        # 5. DB 업데이트
        try:
            project.domain = new_domain
            self.db.commit()
            logger.info(f"Domain changed successfully: {old_domain} -> {new_domain}")
        except Exception as e:
            logger.error(f"Failed to update domain in DB: {e}", exc_info=True)
            self.db.rollback()
            raise HTTPException(status_code=500, detail="도메인 변경 중 오류가 발생했습니다.")

        return {
            "project_id": project.project_id,
            "old_domain": old_domain,
            "new_domain": new_domain
        }
