import pytest

from jina import Flow, __default_host__
from jina.helper import get_internal_ip, get_public_ip


@pytest.mark.parametrize('local_ip, on_public', [(get_internal_ip(), False),
                                                 (get_public_ip(), True)])
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


@pytest.mark.parametrize('local_ip, on_public', [(get_internal_ip(), False),
                                                 (get_public_ip(), True)])
def test_remote_pod_local_pod_local_gateway(local_ip, on_public):
    remote_ip = '111.111.111.111'
    f = Flow(expose_public=on_public).add(host=remote_ip).add()
    f.build()
    for k, v in f._pod_nodes.items():
        print(f'{v.name}\tIN: {v.address_in}\t{v.address_out}')
    assert f['pod0'].host_in == __default_host__
    assert f['pod0'].host_out == local_ip
    assert f['pod1'].host_in == __default_host__
    assert f['pod1'].host_out == __default_host__
    assert f['gateway'].host_in == __default_host__
    assert f['gateway'].host_out == remote_ip


@pytest.mark.parametrize('local_ip, on_public', [(get_internal_ip(), False),
                                                 (get_public_ip(), True)])
def test_remote_pod_local_pod_remote_pod_local_gateway(local_ip, on_public):
    remote1 = '111.111.111.111'
    remote2 = '222.222.222.222'

    f = Flow(expose_public=on_public).add(host=remote1).add().add(host=remote2)
    f.build()
    for k, v in f._pod_nodes.items():
        print(f'{v.name}\tIN: {v.address_in}\t{v.address_out}')

    assert f['pod0'].host_in == __default_host__
    assert f['pod0'].host_out == local_ip
    assert f['pod1'].host_in == __default_host__
    assert f['pod1'].host_out == remote2
    assert f['pod2'].host_in == __default_host__
    assert f['pod2'].host_out == __default_host__
    assert f['gateway'].host_in == remote2
    assert f['gateway'].host_out == remote1


@pytest.mark.parametrize('local_ip, on_public', [(get_internal_ip(), False),
                                                 (get_public_ip(), True)])
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
