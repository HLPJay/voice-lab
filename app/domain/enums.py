from enum import Enum


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    processing = "processing"
    success = "success"
    failed = "failed"


class JobType(str, Enum):
    sync_render = "sync_render"
    async_render = "async_render"
    stream_render = "stream_render"


class BindingStatus(str, Enum):
    available = "available"
    deprecated = "deprecated"


class Provider(str, Enum):
    mock = "mock"
    minimax = "minimax"


class ProviderVoiceStatus(str, Enum):
    available = "available"
    deprecated = "deprecated"
