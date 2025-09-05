"""Common HTTP exception utilities for FastAPI endpoints."""

from fastapi import HTTPException

from core.utils.constants import HTTP_BAD_REQUEST, HTTP_FORBIDDEN, HTTP_INTERNAL_ERROR


def bad_request(detail: str) -> HTTPException:
    """Create a standard 400 Bad Request exception."""
    return HTTPException(status_code=HTTP_BAD_REQUEST, detail=detail)


def forbidden(detail: str) -> HTTPException:
    """Create a standard 403 Forbidden exception."""
    return HTTPException(status_code=HTTP_FORBIDDEN, detail=detail)


def internal_error(detail: str) -> HTTPException:
    """Create a standard 500 Internal Server Error exception."""
    return HTTPException(status_code=HTTP_INTERNAL_ERROR, detail=detail)


def bad_request_from_exception(e: Exception) -> HTTPException:
    """Create a 400 exception from another exception."""
    return bad_request(str(e))
