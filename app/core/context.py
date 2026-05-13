from contextvars import ContextVar, Token

request_id_var: ContextVar[str] = ContextVar("request_id", default="")
job_id_var: ContextVar[str] = ContextVar("job_id", default="")


def get_request_id() -> str:
    return request_id_var.get()


def get_job_id() -> str:
    return job_id_var.get()


def set_job_id(job_id: str) -> Token:
    """Set the current job ID in the context and return token for reset."""
    return job_id_var.set(job_id)


def reset_job_id(token: Token) -> None:
    """Reset job ID context to previous value using the token from set_job_id."""
    job_id_var.reset(token)
