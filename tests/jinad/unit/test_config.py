import pytest

from daemon.config import FastAPIConfig, OpenAPITags, ServerConfig, JinaDConfig


def test_valid_fastapi_config():
    assert FastAPIConfig(NAME='blah').NAME == 'blah'
    assert FastAPIConfig(DESCRIPTION='blah').DESCRIPTION == 'blah'
    assert FastAPIConfig(VERSION='blah').VERSION == 'blah'


def test_invalid_fastapi_config():
    with pytest.raises(ValueError):
        FastAPIConfig(NAME=[])

    with pytest.raises(ValueError):
        FastAPIConfig(DESCRIPTION=[])

    with pytest.raises(ValueError):
        FastAPIConfig(VERSION=[])

    with pytest.raises(ValueError):
        FastAPIConfig(PREFIX=())


def test_valid_openapi_config():
    assert OpenAPITags(API_TAGS=[1]).API_TAGS == [1]
    assert OpenAPITags(FLOW_API_TAGS=[1]).FLOW_API_TAGS == [1]
    assert OpenAPITags(POD_API_TAGS=[1]).POD_API_TAGS == [1]
    assert OpenAPITags(PEA_API_TAGS=[1]).PEA_API_TAGS == [1]
    assert OpenAPITags(LOG_API_TAGS=[1]).LOG_API_TAGS == [1]


def test_invalid_openapi_config():
    with pytest.raises(ValueError):
        OpenAPITags(API_TAGS='abc')

    with pytest.raises(ValueError):
        OpenAPITags(FLOW_API_TAGS=5)

    with pytest.raises(ValueError):
        OpenAPITags(POD_API_TAGS=5.0)

    with pytest.raises(ValueError):
        OpenAPITags(PEA_API_TAGS=True)

    with pytest.raises(ValueError):
        OpenAPITags(LOG_API_TAGS=0)


def test_valid_server_config():
    # TODO: this should be a ipaddress.IPv4Address instead of str
    _hc_host = ServerConfig(HOST='132.90.1.5')
    assert _hc_host.HOST == '132.90.1.5'
    assert _hc_host.PORT == 8000

    _hc_port = ServerConfig(PORT=1200)
    assert _hc_port.HOST == '0.0.0.0'
    assert _hc_port.PORT == 1200


def test_invalid_server_config():
    with pytest.raises(ValueError):
        ServerConfig(HOST=[])

    with pytest.raises(ValueError):
        ServerConfig(PORT='abc')


def test_valid_jinad_config():
    assert JinaDConfig(CONTEXT='flow').CONTEXT == 'flow'
    assert JinaDConfig(CONTEXT='pod').CONTEXT == 'pod'
    assert JinaDConfig(CONTEXT='pea').CONTEXT == 'pea'
    assert JinaDConfig(CONTEXT='all').CONTEXT == 'all'


def test_invalid_jinad_config():
    with pytest.raises(ValueError):
        JinaDConfig(CONTEXT='anything else')
