import traceback

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class DockerNotFoundException(Exception):
    """ Exception if docker client cannot communicate with dockerd"""


class DockerImageException(Exception):
    """ Exception while handling a docker image in the workspace"""


class DockerNetworkException(Exception):
    """ Exception while handling docker networks in the workspace """


class DockerContainerException(Exception):
    """ Exception while handling a docker container in the workspace"""


class Runtime400Exception(Exception):
    """Exception when daemon FastAPI app is running"""


async def daemon_runtime_exception_handler(request: Request, ex: 'Runtime400Exception'):
    """Exception handler for all Runtime400Exceptions

    :param request: starlette request
    :param ex: actual Runtime400Exception
    :return: json response representing the error
    """
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


async def validation_exception_handler(request: Request, ex: 'RequestValidationError'):
    """Exception handler for all RequestValidationError raised by pydantic

    :param request: starlette request
    :param ex: actual Validation exception
    :return: json response representing the error
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": ex.errors(), "body": str(ex)}),
    )
