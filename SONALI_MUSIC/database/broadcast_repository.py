import time
import uuid
import logging
from typing import Dict, Any, List, Optional
from SONALI_MUSIC.core.mongo import mongodb

logger = logging.getLogger(__name__)

broadcast_db = mongodb.broadcast_jobs

class BroadcastRepository:
    async def create_job(
        self,
        sender_id: int,
        broadcast_type: str, # "main", "cbroadcast", "individual"
        target_type: str, # "user", "group", "all", "owner"
        total_targets: int,
        content: Dict[str, Any],
        dry_run: bool = False
    ) -> str:
        job_id = str(uuid.uuid4())
        now = time.time()
        job_record = {
            "job_id": job_id,
            "created_by": sender_id,
            "broadcast_type": broadcast_type,
            "target_type": target_type,
            "total_targets": total_targets,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "floodwait_count": 0,
            "started_at": now,
            "completed_at": None,
            "cancelled": False,
            "dry_run": dry_run,
            "status": "QUEUED", # QUEUED, RUNNING, COMPLETED, PARTIAL, CANCELLED, FAILED
            "error_summary": [],
            "content": content
        }
        await broadcast_db.insert_one(job_record)
        return job_id

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return await broadcast_db.find_one({"job_id": job_id})

    async def update_progress(
        self,
        job_id: str,
        successful: int,
        failed: int,
        skipped: int,
        floodwait_count: int,
        status: str = "RUNNING"
    ):
        await broadcast_db.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "successful": successful,
                    "failed": failed,
                    "skipped": skipped,
                    "floodwait_count": floodwait_count,
                    "status": status,
                    "updated_at": time.time()
                }
            }
        )

    async def finalize_job(
        self,
        job_id: str,
        status: str,
        cancelled: bool = False,
        error_summary: Optional[List[str]] = None
    ):
        update_fields = {
            "status": status,
            "cancelled": cancelled,
            "completed_at": time.time()
        }
        if error_summary:
            update_fields["error_summary"] = error_summary
        await broadcast_db.update_one({"job_id": job_id}, {"$set": update_fields})

broadcast_repo = BroadcastRepository()
