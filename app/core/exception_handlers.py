import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import KayroError


logger = logging.getLogger(__name__)


async def kayro_exception_handler(
    request: Request,
    exc: KayroError
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "detail": exc.message,
            "path": str(request.url.path)
        }
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
):
    logger.exception("Unhandled exception")

    return JSONResponse(
        status_code=500,
        content={
            "error": exc.__class__.__name__,
            "detail": str(exc),
            "path": str(request.url.path),
        }
    )
