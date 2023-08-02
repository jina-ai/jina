import traceback

import grpc.aio
import pytest
from grpc import StatusCode
from grpc.aio import Metadata

from jina.excepts import BaseJinaException, ExecutorError, InternalNetworkError


@pytest.fixture
def aio_rpc_error():
    return grpc.aio.AioRpcError(StatusCode.OK, None, None, details='I am a grpc error')


def test_ine_parent_classes(aio_rpc_error):
    err = InternalNetworkError(aio_rpc_error)
    # check that it can be caught when we expect AioRpcError or BaseJinaException
    with pytest.raises(grpc.aio.AioRpcError):
        raise err
    with pytest.raises(BaseJinaException):
        raise err


def test_ine_statuscode(aio_rpc_error):
    err = InternalNetworkError(aio_rpc_error)
    assert err.code() == aio_rpc_error.code()


def test_ine_details(aio_rpc_error):
    err = InternalNetworkError(aio_rpc_error)
    assert err.details() == aio_rpc_error.details()
    err = InternalNetworkError(aio_rpc_error, details='I am not a normal grpc error!')
    assert err.details() == 'I am not a normal grpc error!'
    assert str(err) == 'I am not a normal grpc error!'


@pytest.mark.parametrize('metadata', [None, Metadata(('content-length', '0'))])
def test_ine_trailing_metadata(metadata):
    aio_rpc_error = grpc.aio.AioRpcError(
        StatusCode.OK,
        None,
        trailing_metadata=metadata,
        details='I am a grpc error',
    )
    err = InternalNetworkError(aio_rpc_error)
    if metadata:
        assert (
            str(err)
            == 'I am a grpc error\ntrailing_metadata=Metadata(((\'content-length\', \'0\'),))'
        )
    else:
        assert str(err) == 'I am a grpc error'


@pytest.mark.parametrize(
    'exception_args', [['value error'], ['value error', 'zero length']]
)
@pytest.mark.parametrize('executor', [None, 'TestExecutor'])
def test_executor_error(exception_args, executor):
    custom_exception = ValueError(exception_args)
    exception_stack = traceback.format_exception(
        type(custom_exception),
        value=custom_exception,
        tb=custom_exception.__traceback__,
    )

    executor_error = ExecutorError(
        name=custom_exception.__class__.__name__,
        args=exception_args,
        stacks=exception_stack,
        executor=executor,
    )
    assert executor_error.name == 'ValueError'
    assert executor_error.args == exception_args
    assert executor_error.stacks == exception_stack
    assert executor_error.executor == executor
    assert str(executor_error) == f'ValueError: {exception_args}\n'
