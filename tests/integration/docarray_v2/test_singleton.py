import pytest


@pytest.mark.parametrize('ctxt_manager', ['flow', 'deployment'])
@pytest.mark.parametrize('protocol', [['grpc'], ['http'], ['http', 'grpc', 'websocket']])
def test_singleton_return(ctxt_manager, protocol):
    pass


@pytest.mark.parametrize('ctxt_manager', ['flow', 'deployment'])
@pytest.mark.parametrize('protocol', [['grpc'], ['http'], ['http', 'grpc', 'websocket']])
def test_singleton_in_place(ctxt_manager, protocol):
    pass


@pytest.mark.parametrize('protocol', [['grpc'], ['http'], ['http', 'grpc']])
def test_singleton_in_flow_in_the_middle(protocol):
    pass


def test_openapi_json():
    pass

@pytest.mark.parametrize('ctxt_manager', ['flow', 'deployment'])
def test_calL_from_requests_as_singleton(ctxt_manager):
    pass


@pytest.mark.parametrize('ctxt_manager', ['flow', 'deployment'])
@pytest.mark.parametrize('protocol', [['grpc'], ['http'], ['http', 'grpc']])
def test_client_singleton_return_type(ctxt_manager, protocol):
    pass

