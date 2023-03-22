import asyncio
import random

import aiohttp
import grpc


async def wait_or_raise_err(
    attempt: int,
    err: Exception,
    max_attempts: float,
    backoff_multiplier: float,
    initial_backoff: float,
    max_backoff: float,
):
    """
    Accepts retry parameters and the underlying. The error is raised if the max_attempts has been reached otherwise the
    method waits based on the backoff calculations.
    :param attempt: Number of the current attempt.
    :param err: Underlying error that was raised by the operation.
    :param max_attempts: Maximum number of attempts that are allowed.
    :param backoff_multiplier: Factor that will be raised to the exponent of (attempt - 1) for calculating the backoff wait time.
    :param initial_backoff: The backoff time on the first error. This will be multiplied by the backoff_multiplier exponent for subsequent wait time calculations.
    :param max_backoff: The maximum backoff wait time.
    """
    if attempt == max_attempts:
        if isinstance(err, asyncio.CancelledError):
            trailing_metadata = grpc.aio.Metadata()
            trailing_metadata.add('jina-client-attempts', str(attempt))
            raise grpc.aio.AioRpcError(
                code=grpc.StatusCode.CANCELLED,
                initial_metadata=grpc.aio.Metadata(),
                trailing_metadata=trailing_metadata,
            )
        elif isinstance(err, grpc.aio.AioRpcError):
            trailing_metadata = err.trailing_metadata() or grpc.aio.Metadata()
            trailing_metadata.add('jina-client-attempts', str(attempt))
            raise grpc.aio.AioRpcError(
                code=err.code(),
                details=err.details(),
                initial_metadata=err.initial_metadata(),
                trailing_metadata=trailing_metadata,
                debug_error_string=err.debug_error_string(),
            )
        elif isinstance(err, aiohttp.ClientConnectorCertificateError):
            raise err
        elif isinstance(err, aiohttp.ClientError):
            raise ConnectionError(str(err))
        else:
            raise err
    else:
        await _backoff_wait(attempt, backoff_multiplier, initial_backoff, max_backoff)


async def _backoff_wait(attempt, backoff_multiplier, initial_backoff, max_backoff):
    if attempt == 1:
        wait_time = initial_backoff
    else:
        wait_time = random.uniform(
            0,
            min(initial_backoff * backoff_multiplier ** (attempt - 1), max_backoff),
        )
    await asyncio.sleep(wait_time)
