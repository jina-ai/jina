from argparse import Namespace

from jina.enums import PollingType
from jina.peapods.remote import namespace_to_dict


def test_namespace_to_dict():
    _namespaces = {
        'head': Namespace(host='1.2.3.4', name='encoder', parallel=2, pea_id=-1, polling=PollingType.ANY,
                          port_ctrl=39011, port_expose=8000, uses_after='_pass', uses_before=None),
        'tail': Namespace(host='1.2.3.4', name='encoder', parallel=2, pea_id=-1, polling=PollingType.ANY,
                          port_ctrl=46937, port_expose=8000, uses_after='_pass', uses_before=None),
        'peas': [
            Namespace(host='1.2.3.4', name='encoder', parallel=2, pea_id=-1, polling=PollingType.ANY,
                      port_ctrl=44747, port_expose=8000, uses='helloworld.encoder.yml', uses_after='_pass',
                      uses_before=None),
            Namespace(host='1.2.3.4', name='encoder', parallel=2, pea_id=-1, polling=PollingType.ANY,
                      port_ctrl=48957, port_expose=8000, uses='helloworld.encoder.yml', uses_after='_pass',
                      uses_before=None)
        ]
    }
    _dict_args = namespace_to_dict(args=_namespaces)
    assert 'head' in _dict_args
    assert 'tail' in _dict_args
    assert 'peas' in _dict_args
    assert len(_dict_args['peas']) == 2
    assert _namespaces['head'].polling.value == _dict_args['head']['polling']
    assert _namespaces['peas'][0].uses == _dict_args['peas'][0]['uses']
