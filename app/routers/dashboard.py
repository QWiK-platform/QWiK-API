from fastapi import APIRouter, Depends

from app.models.models import User
from app.dependencies import get_current_user


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("")
async def get_dashboard(current_user: User = Depends(get_current_user)):

    return {
        "projects": [
            {
                "project_id": 1,
                "username": "ta3wook",
                "usage": {
                    "storage_used": 240,
                    "traffic_used": 1200,
                },
                "repo_name": "QWiK-FE",
                "domain": "qwik-fe.qwik.com",
                "status": True,
                "created_at": "2025-12-16T11:11:11",
                "commit_message": "feat: changed layout",
                "reload_at": "2025-12-16T12:12:12"
            },
            {
                "project_id": 2,
                "username": "ta3wook",
                "usage": {
                    "storage_used": 512,
                    "traffic_used": 2400,
                },
                "repo_name": "QWiK-API",
                "domain": "qwik-api.qwik.com",
                "status": True,
                "created_at": "2025-12-15T09:30:00",
                "commit_message": "fix: database connection pool optimization",
                "reload_at": "2025-12-17T14:22:33"
            },
            {
                "project_id": 3,
                "username": "ta3wook",
                "usage": {
                    "storage_used": 128,
                    "traffic_used": 800,
                },
                "repo_name": "portfolio-site",
                "domain": "portfolio.qwik.com",
                "status": True,
                "created_at": "2025-12-14T16:45:00",
                "commit_message": "chore: update dependencies",
                "reload_at": "2025-12-18T08:15:20"
            },
            {
                "project_id": 4,
                "username": "ta3wook",
                "usage": {
                    "storage_used": 64,
                    "traffic_used": 400,
                },
                "repo_name": "blog-engine",
                "domain": "blog.qwik.com",
                "status": False,
                "created_at": "2025-12-10T13:20:00",
                "commit_message": "feat: add markdown editor",
                "reload_at": "2025-12-11T10:05:15"
            },
            {
                "project_id": 5,
                "username": "ta3wook",
                "usage": {
                    "storage_used": 320,
                    "traffic_used": 1800,
                },
                "repo_name": "e-commerce-platform",
                "domain": "shop.qwik.com",
                "status": True,
                "created_at": "2025-12-12T10:00:00",
                "commit_message": "feat: implement payment gateway integration",
                "reload_at": "2025-12-19T16:40:50"
            },
            {
                "project_id": 6,
                "username": "ta3wook",
                "usage": {
                    "storage_used": 180,
                    "traffic_used": 950,
                },
                "repo_name": "task-manager",
                "domain": "tasks.qwik.com",
                "status": True,
                "created_at": "2025-12-08T14:30:00",
                "commit_message": "refactor: improve task filtering logic",
                "reload_at": "2025-12-18T20:10:30"
            }
        ]
    }