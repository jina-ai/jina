import traceback

from fastapi import Request
from fastapi.responses import JSONResponse


class Runtime400Exception(Exception):
    """Exception when daemon FastAPI app is running"""


async def daemon_runtime_exception_handler(request: Request, ex: 'Runtime400Exception'):
    return JSONResponse(
        status_code=400,
        content={
            'detail': repr(ex),
            'body': traceback.format_exception(
                etype=type(ex), value=ex, tb=ex.__traceback__
            ),
        },
    )
