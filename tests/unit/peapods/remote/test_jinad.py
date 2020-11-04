import mock

from jina.logging import JinaLogger
from jina.peapods.jinad import JinadAPI, PodAPI, PeaAPI, fetch_files_from_yaml


logger = JinaLogger(context='test-remote')
yaml_path = 'tests/unit/peapods/remote'
jinad_api = JinadAPI(host='0.0.0.0', port=8000, logger=logger)
pod_api = PodAPI(host='0.0.0.0', port=8000, logger=logger)
pea_api = PeaAPI(host='0.0.0.0', port=8000, logger=logger)


def test_fetch_files_from_yaml_pods():
    pea_args = {
        'head': None,
        'tail': None,
        'peas': [
            {
                'name': 'encode',
                'uses': f'{yaml_path}/yamls/encoder.yml',
                'py_modules': None,
                'uses_before': None,
                'uses_after': None
            },
            {
                'name': 'index',
                'uses': f'{yaml_path}/yamls/indexer.yml',
                'py_modules': None,
                'uses_before': None,
                'uses_after': None
            },
        ]
    }
    _uses_files, _pymodule_files = fetch_files_from_yaml(pea_args, logger)
    assert _uses_files == {f'{yaml_path}/yamls/encoder.yml',
                           f'{yaml_path}/yamls/indexer.yml'}
    assert _pymodule_files == {f'{yaml_path}/yamls/dummy.py'}


def test_fetch_files_from_yaml_pea():
    pea_args = {
        'name': 'encode',
        'uses': f'{yaml_path}/yamls/encoder.yml',
        'py_modules': None,
        'uses_before': None,
        'uses_after': None
    }
    _uses_files, _pymodule_files = fetch_files_from_yaml(pea_args, logger)
    assert _uses_files == {f'{yaml_path}/yamls/encoder.yml'}
    assert _pymodule_files == {f'{yaml_path}/yamls/dummy.py'}


@mock.patch('requests.get')
def test_jinad_is_alive(mocker):
    mocker.return_value.status_code = 200
    assert jinad_api.is_alive()

    mocker.return_value.status_code = 404
    assert not jinad_api.is_alive()


@mock.patch('requests.put')
def test_jinad_create(mocker):
    mocker.return_value.status_code = 200
    mocker.return_value.json.return_value = {'blah_id': 'abcd'}
    assert jinad_api.create(kind='blah', pea_args={}) == 'abcd'

    mocker.return_value.status_code = 404
    assert not jinad_api.create(kind='blah', pea_args={})


@mock.patch('requests.delete')
def test_jinad_delete(mocker):
    mocker.return_value.status_code = 200
    assert jinad_api.delete(kind='blah', remote_id='abcd')

    mocker.return_value.status_code = 404
    assert not jinad_api.delete(kind='blah', remote_id='abcd')


@mock.patch('requests.put')
def test_podapi_create(mocker):
    mocker.return_value.status_code = 200
    mocker.return_value.json.return_value = {'pod_id': 'abcd'}
    assert pod_api.create(pea_args={}) == 'abcd'

    mocker.return_value.status_code = 404
    assert not pod_api.create(pea_args={})


@mock.patch('requests.delete')
def test_podapi_delete(mocker):
    mocker.return_value.status_code = 200
    assert pod_api.delete(pod_id='abcd')

    mocker.return_value.status_code = 404
    assert not pod_api.delete(pod_id='abcd')


@mock.patch('requests.put')
def test_peaapi_create(mocker):
    mocker.return_value.status_code = 200
    mocker.return_value.json.return_value = {'pea_id': 'abcd'}
    assert pea_api.create(pea_args={}) == 'abcd'

    mocker.return_value.status_code = 404
    assert not pea_api.create(pea_args={})


@mock.patch('requests.delete')
def test_peaapi_delete(mocker):
    mocker.return_value.status_code = 200
    assert pea_api.delete(pea_id='abcd')

    mocker.return_value.status_code = 404
    assert not pea_api.delete(pea_id='abcd')
