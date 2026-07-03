from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import KayroError


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
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "detail": "Unexpected server error",
            "path": str(request.url.path)
        }
    )
