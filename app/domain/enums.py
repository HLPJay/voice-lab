from enum import Enum


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"


class JobType(str, Enum):
    sync_render = "sync_render"
