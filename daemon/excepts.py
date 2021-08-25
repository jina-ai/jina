import traceback
from http import HTTPStatus
from typing import List, Union

from fastapi import Request
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
    """Exception for all errors in Daemon

    - Should only be used in `api/endpoints/*.py`.
    - Should always be chained.
    - Handled by `daemon_runtime_exception_handler`
    """


class PartialDaemon400Exception(Exception):
    """Exception for all errors in Partial Daemon

    This can be raised from 2 places:
    1. Inside partial daemon:
       - Should always be chained and raised in `a[i/partial/endpoints/*.py`.
       - This way it has a `__cause__` and stacktrace can be retrieved in `partial_daemon_exception_handler`
    2. Inside main store:
       - Should be raised whenever main-daemon receives a 400 from partial-daemon.
       - Don't chain it. Raise it like - `PartialDaemon400Exception('original traceback')`
       - Gets handled via `daemon_runtime_exception_handler` when chained with `Runtime400Exception`
    """

    def __init__(self, message: Union[List, str] = None, *args: object) -> None:
        self.message = message


class PartialDaemonConnectionException(PartialDaemon400Exception):
    """ Exception if JinaD cannot connect to Partial Daemon"""


def _get_exception(ex: Exception) -> Exception:
    """Get exception cause/context from chained exceptions

    :param ex: chained exception
    :return: cause of chained exception if any
    """
    if ex.__cause__:
        return ex.__cause__
    elif ex.__context__:
        return ex.__context__
    else:
        return ex


def json_response(status_code: HTTPStatus, detail: str, body: str) -> JSONResponse:
    """json response from status, detail & body

    :param status_code: http status code
    :param detail: exception name in detail
    :param body: error stacktrace
    :return: JSONResponse object
    """
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(
            {
                'detail': detail,
                'body': body,
            }
        ),
    )


async def partial_daemon_exception_handler(
    request: Request, ex: 'PartialDaemon400Exception'
):
    """Exception handler for all PartialDaemon400Exceptions

    Since `PartialDaemon400Exception` is always chained, we access the `__cause__` and send that as `body`.

    This handler makes sure, in case of exceptions (Pea/Pod/Flow start/update/delete failures),
    the response from Partial Daemon whould always look like -
    ```{
        "detail": "PartialDaemon400Exception",
        "body": [
            "stack trace line1"
            "stack trace line2:
        ]
    }```

    :param request: starlette request
    :param ex: actual PartialDaemon400Exception
    :return: json response representing the error
    """
    exception = _get_exception(ex)
    return json_response(
        status_code=HTTPStatus.BAD_REQUEST,
        detail=ex.__class__.__name__,
        body=traceback.format_exception(
            etype=type(exception), value=exception, tb=exception.__traceback__
        ),
    )


async def daemon_runtime_exception_handler(request: Request, ex: 'Runtime400Exception'):
    """Exception handler for all Runtime400Exceptions

    `Runtime400Exception` is always chained.

    - When `__cause__` is `PartialDaemon400Exception`, we know, it is due to an error inside the
      Partial Daemon container and `ex.message` carries the actual stack trace.
    - All other errors are inside the main Daemon itself, so we get the stack trace using traceback.

    :param request: starlette request
    :param ex: actual Runtime400Exception
    :return: json response representing the error
    """
    exception = _get_exception(ex)
    return json_response(
        status_code=HTTPStatus.BAD_REQUEST,
        detail=ex.__class__.__name__,
        body=exception.message
        if isinstance(exception, PartialDaemon400Exception)
        else traceback.format_exception(
            etype=type(exception), value=exception, tb=exception.__traceback__
        ),
    )


async def validation_exception_handler(request: Request, ex: 'RequestValidationError'):
    """Exception handler for all RequestValidationError raised by pydantic

    :param request: starlette request
    :param ex: actual Validation exception
    :return: json response representing the error
    """
    return json_response(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        detail=ex.errors(),
        body=str(ex),
    )
