import grpc.aio
import pytest
from grpc import StatusCode
from grpc.aio import Metadata

from jina.excepts import BaseJinaException, InternalNetworkError


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
