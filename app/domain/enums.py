from enum import Enum


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"


class JobType(str, Enum):
    sync_render = "sync_render"


class BindingStatus(str, Enum):
    available = "available"
    deprecated = "deprecated"


class Provider(str, Enum):
    mock = "mock"
    minimax = "minimax"


class ProviderVoiceStatus(str, Enum):
    available = "available"
    deprecated = "deprecated"
