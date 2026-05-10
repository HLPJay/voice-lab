from enum import StrEnum


class JobStatus(StrEnum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"


class JobType(StrEnum):
    sync_render = "sync_render"
