import asyncio
from typing import Dict

class BroadcastCancellationManager:
    def __init__(self):
        self._tokens: Dict[str, asyncio.Event] = {}

    def create_token(self, job_id: str) -> asyncio.Event:
        event = asyncio.Event()
        self._tokens[job_id] = event
        return event

    def cancel_job(self, job_id: str) -> bool:
        if job_id in self._tokens:
            self._tokens[job_id].set()
            return True
        return False

    def is_cancelled(self, job_id: str) -> bool:
        if job_id in self._tokens:
            return self._tokens[job_id].is_set()
        return False

    def remove_token(self, job_id: str):
        self._tokens.pop(job_id, None)

cancellation_manager = BroadcastCancellationManager()
