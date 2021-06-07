import traceback

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError


class DockerNotFoundException(Exception):
    """ Exception if docker client cannot communicate with dockerd"""


class DockerBuildException(Exception):
    """ Exception while building a docker image in the workspace"""


class DockerNetworkException(Exception):
    """ Exception while handling docker networks in the workspace """


class DockerRunException(Exception):
    """ Exception while starting a docker image in the workspace"""


class Runtime400Exception(Exception):
    """Exception when daemon FastAPI app is running"""


async def daemon_runtime_exception_handler(request: Request, ex: 'Runtime400Exception'):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(
            {
                'detail': repr(ex),
                'body': traceback.format_exception(
                    etype=type(ex), value=ex, tb=ex.__traceback__
                ),
            }
        ),
    )


async def validation_exception_handler(request: Request, exc: 'RequestValidationError'):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": str(exc)}),
    )
