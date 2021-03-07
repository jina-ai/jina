import pytest

from jina import Flow, __default_host__
from jina.enums import SocketType
from jina.helper import get_internal_ip, get_public_ip


@pytest.mark.parametrize(
    'local_ip, on_public', [(get_internal_ip(), False), (get_public_ip(), True)]
)
def test_remote_pod_local_gateway(local_ip, on_public):
    # BIND socket's host must always be 0.0.0.0
    remote_ip = '111.111.111.111'
    f = Flow(expose_public=on_public).add(host=remote_ip)
    f.build()
    for k, v in f:
        print(f'{v.name}\tIN: {v.address_in}\t{v.address_out}')
    assert f['pod0'].host_in == __default_host__
    assert f['pod0'].host_out == __default_host__
    assert f['gateway'].host_in == remote_ip
    assert f['gateway'].host_out == remote_ip


@pytest.mark.parametrize(
    'local_ip, on_public', [(get_internal_ip(), False), (get_public_ip(), True)]
)
def test_remote_pod_local_pod_local_gateway_input_socket_pull_connect_from_remote(
    local_ip, on_public
):
    remote_ip = '111.111.111.111'
    f = Flow(expose_public=on_public).add(host=remote_ip).add().build()
    for k, v in f:
        print(f'{v.name}\tIN: {v.address_in}\t{v.address_out}')
    assert f['pod0'].host_in == __default_host__
    assert f['pod0'].host_out == __default_host__
    assert f['pod1'].host_in == remote_ip
    assert f['pod1'].host_out == __default_host__
    assert f['gateway'].host_in == __default_host__
    assert f['gateway'].host_out == remote_ip


@pytest.mark.parametrize(
    'local_ip, on_public', [(get_internal_ip(), False), (get_public_ip(), True)]
)
def test_remote_pod_local_pod_local_gateway(local_ip, on_public):
    remote_ip = '111.111.111.111'
    f = Flow(expose_public=on_public).add(host=remote_ip).add().build()
    for k, v in f:
        print(f'{v.name}\tIN: {v.address_in}\t{v.address_out}')
    assert f['pod0'].host_in == __default_host__
    assert f['pod0'].host_out == __default_host__
    assert f['pod1'].host_in == remote_ip
    assert f['pod1'].host_out == __default_host__
    assert f['gateway'].host_in == __default_host__
    assert f['gateway'].host_out == remote_ip


@pytest.mark.parametrize(
    'local_ip, on_public', [(get_internal_ip(), False), (get_public_ip(), True)]
)
def test_remote_pod_local_pod_remote_pod_local_gateway_input_socket_pull_connect_from_remote(
    local_ip, on_public
):
    remote1 = '111.111.111.111'
    remote2 = '222.222.222.222'

    f = Flow(expose_public=on_public).add(host=remote1).add().add(host=remote2).build()
    for k, v in f:
        print(f'{v.name}\tIN: {v.address_in}\t{v.address_out}')

    assert f['pod0'].host_in == __default_host__
    assert f['pod0'].host_out == __default_host__
    assert f['pod1'].host_in == remote1
    assert f['pod1'].host_out == remote2
    assert f['pod2'].host_in == __default_host__
    assert f['pod2'].host_out == __default_host__
    assert f['gateway'].host_in == remote2
    assert f['gateway'].host_out == remote1


@pytest.mark.parametrize(
    'local_ip, on_public', [(get_internal_ip(), False), (get_public_ip(), True)]
)
def test_remote_pod_local_pod_remote_pod_local_gateway(local_ip, on_public):
    remote1 = '111.111.111.111'
    remote2 = '222.222.222.222'

    f = Flow(expose_public=on_public).add(host=remote1).add().add(host=remote2).build()
    for k, v in f:
        print(f'{v.name}\tIN: {v.address_in}\t{v.address_out}')

    assert f['pod0'].host_in == __default_host__
    assert f['pod0'].host_out == __default_host__
    assert f['pod1'].host_in == remote1
    assert f['pod1'].host_out == remote2
    assert f['pod2'].host_in == __default_host__
    assert f['pod2'].host_out == __default_host__
    assert f['gateway'].host_in == remote2
    assert f['gateway'].host_out == remote1


@pytest.mark.parametrize(
    'local_ip, on_public', [(get_internal_ip(), False), (get_public_ip(), True)]
)
def test_local_pod_remote_pod_remote_pod_local_gateway(local_ip, on_public):
    remote1 = '111.111.111.111'
    remote2 = '222.222.222.222'

    f = Flow(expose_public=on_public).add().add(host=remote1).add(host=remote2)
    f.build()

    for k, v in f:
        print(f'{v.name}\tIN: {v.address_in}\t{v.address_out}')
    assert f['pod0'].host_in == __default_host__
    assert f['pod0'].host_out == remote1
    assert f['pod1'].host_in == __default_host__
    assert f['pod1'].host_out == remote2
    assert f['pod2'].host_in == __default_host__
    assert f['pod2'].host_out == __default_host__
    assert f['gateway'].host_in == remote2
    assert f['gateway'].host_out == __default_host__


def test_gateway_remote():
    remote1 = '111.111.111.111'
    f = Flow().add(host=remote1).build()
    for k, v in f:
        print(f'{v.name}\tIN: {v.address_in}\t{v.address_out}')

    assert f['pod0'].host_in == __default_host__
    assert f['pod0'].host_out == __default_host__
    assert f['pod0'].args.socket_in.is_bind
    assert f['pod0'].args.socket_out.is_bind
    assert f['gateway'].host_in == remote1
    assert f['gateway'].host_out == remote1


def test_gateway_remote_local():
    """

    remote  IN: 0.0.0.0:61913 (PULL_BIND)   internal_ip:61914 (PUSH_CONNECT)
    pod1    IN: 0.0.0.0:61914 (PULL_BIND)    0.0.0.0:61918 (PUSH_BIND)
    gateway IN: 0.0.0.0:61918 (PULL_CONNECT)  111.111.111.111:61913 (PUSH_CONNECT)

    :return:
    """
    remote1 = '111.111.111.111'
    f = Flow().add(host=remote1).add().build()
    for k, v in f:
        print(f'{v.name}\tIN: {v.address_in}\t{v.address_out}')

    assert f['pod0'].host_in == __default_host__
    assert f['pod0'].host_out == __default_host__
    assert f['pod0'].args.socket_in == SocketType.PULL_BIND
    assert f['pod0'].args.socket_out == SocketType.PUSH_BIND

    assert f['pod1'].host_in == remote1
    assert f['pod1'].host_out == __default_host__
    assert f['pod1'].args.socket_in == SocketType.PULL_CONNECT
    assert f['pod1'].args.socket_out == SocketType.PUSH_BIND
    assert f['gateway'].host_in == __default_host__
    assert f['gateway'].host_out == remote1
    assert f['gateway'].args.socket_in == SocketType.PULL_CONNECT
    assert f['gateway'].args.socket_out == SocketType.PUSH_CONNECT


def test_gateway_remote_local_input_socket_pull_connect_from_remote():
    """

    remote  IN: 0.0.0.0:61913 (PULL_BIND)   0.0.0.0:61914 (PUSH_BIND)
    pod1    IN: 3.135.17.36:61914 (PULL_CONNECT)    0.0.0.0:61918 (PUSH_BIND)
    gateway IN: 0.0.0.0:61918 (PULL_CONNECT)    3.135.17.36:61913 (PUSH_CONNECT)

    :return:
    """
    remote1 = '111.111.111.111'
    f = Flow().add(host=remote1).add().build()
    for k, v in f:
        print(f'{v.name}\tIN: {v.address_in}\t{v.address_out}')

    assert f['pod0'].host_in == __default_host__
    assert f['pod0'].host_out == __default_host__
    assert f['pod0'].args.socket_in.is_bind
    assert f['pod0'].args.socket_out.is_bind
    assert f['pod1'].host_in == remote1
    assert f['pod1'].host_out == __default_host__
    assert not f['pod1'].args.socket_in.is_bind
    assert f['pod1'].args.socket_out.is_bind
    assert f['gateway'].host_in == __default_host__
    assert f['gateway'].host_out == remote1


def test_gateway_local_remote():
    """

    pod0    IN: 0.0.0.0:62322 (PULL_BIND)   3.135.17.36:62326 (PUSH_CONNECT)
    remote  IN: 0.0.0.0:62326 (PULL_BIND)   0.0.0.0:62327 (PUSH_BIND)
    gateway IN: 3.135.17.36:62327 (PULL_CONNECT)    0.0.0.0:62322 (PUSH_CONNECT)

    :return:
    """
    remote1 = '111.111.111.111'
    f = Flow().add().add(host=remote1).build()
    for k, v in f:
        print(f'{v.name}\tIN: {v.address_in}\t{v.address_out}')

    assert f['pod0'].host_in == __default_host__
    assert f['pod0'].host_out == remote1
    assert f['pod0'].args.socket_in.is_bind
    assert not f['pod0'].args.socket_out.is_bind
    assert f['pod1'].host_in == __default_host__
    assert f['pod1'].host_out == __default_host__
    assert f['pod1'].args.socket_in.is_bind
    assert f['pod1'].args.socket_out.is_bind
    assert f['gateway'].host_in == remote1
    assert f['gateway'].host_out == __default_host__
