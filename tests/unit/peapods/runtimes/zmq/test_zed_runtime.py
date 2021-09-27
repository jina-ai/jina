from jina.peapods.runtimes.zmq.zed import ZEDRuntime


def test_zed_runtime_parse_params():
    params = {
        'traversal_path': 'r',
        'param1': 5,
        'executor_name': {'traversal_path': 'c'},
    }

    parsed_params = ZEDRuntime._parse_params(params, 'executor_name')

    assert parsed_params['traversal_path'] == 'c'
    assert parsed_params['param1'] == 5
    assert parsed_params['executor_name']['traversal_path'] == 'c'
