from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="")
job_id_var: ContextVar[str] = ContextVar("job_id", default="")


def get_request_id() -> str:
    return request_id_var.get()


def get_job_id() -> str:
    return job_id_var.get()


def set_job_id(job_id: str) -> None:
    """Set the current job ID in the context."""
    job_id_var.set(job_id)
