import uuid

import pytest
from fastapi import UploadFile

from daemon.api.endpoints import pea

_temp_id = uuid.uuid1()


def mock_pea_start_exception(**kwargs):
    raise pea.PeaStartException


def mock_key_error(**kwargs):
    raise KeyError


@pytest.mark.asyncio
@pytest.mark.parametrize('uses_files, pymodules_files', [
    ([UploadFile(filename='abc.yaml')], [UploadFile(filename='abc.py')]),
    ([UploadFile(filename='abc.yaml'), UploadFile(filename='def.yaml')], [UploadFile(filename='abc.py')]),
    ([UploadFile(filename='abc.yaml')], [UploadFile(filename='abc.py'), UploadFile(filename='def.py')]),
    ([UploadFile(filename='abc.yaml')], []),
    ([], [UploadFile(filename='abc.py')])
])
async def test_upload_success(monkeypatch, uses_files, pymodules_files):
    monkeypatch.setattr(pea, 'create_meta_files_from_upload', lambda *args: None)
    response = await pea._upload(uses_files=uses_files,
                                 pymodules_files=pymodules_files)
    assert response['status_code'] == 200
    assert response['status'] == 'uploaded'


@pytest.mark.asyncio
async def test_upload_failure(monkeypatch):
    monkeypatch.setattr(pea, 'create_meta_files_from_upload', lambda *args: None)
    response = await pea._upload(uses_files=[], pymodules_files=[])
    assert response['status_code'] == 200
    assert response['status'] == 'nothing to upload'


@pytest.mark.asyncio
async def test_create_success(monkeypatch):
    monkeypatch.setattr(pea.pea_store, '_create', lambda **args: _temp_id)
    response = await pea._create(pea.PeaModel())
    assert response['status_code'] == 200
    assert response['pea_id'] == _temp_id
    assert response['status'] == 'started'


@pytest.mark.asyncio
async def test_create_pod_start_exception(monkeypatch):
    monkeypatch.setattr(pea.pea_store, '_create', mock_pea_start_exception)
    with pytest.raises(pea.HTTPException) as response:
        await pea._create(pea.PeaModel())
    assert response.value.status_code == 404
    assert 'Pea couldn\'t get started' in response.value.detail


@pytest.mark.asyncio
async def test_create_any_exception(monkeypatch):
    monkeypatch.setattr(pea.pea_store, '_create', mock_key_error)
    with pytest.raises(pea.HTTPException) as response:
        await pea._create(pea.PeaModel())
    assert response.value.status_code == 404
    assert response.value.detail == 'Something went wrong'


@pytest.mark.asyncio
async def test_delete_success(monkeypatch):
    monkeypatch.setattr(pea.pea_store, '_delete', lambda **kwargs: None)
    response = await pea._delete(_temp_id)
    assert response['status_code'] == 200


@pytest.mark.asyncio
async def test_delete_exception(monkeypatch):
    monkeypatch.setattr(pea.pea_store, '_delete', mock_key_error)
    with pytest.raises(pea.HTTPException) as response:
        await pea._delete(_temp_id)
    assert response.value.status_code == 404
    assert response.value.detail == f'Pea ID {_temp_id} not found! Please create a new Pea'
