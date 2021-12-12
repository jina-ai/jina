import os
from contextlib import contextmanager

from daemon.clients import JinaDClient
from jina.types.request import Response
from jina.helper import random_identity
from jina import Document, Client, __default_host__, Flow

cur_dir = os.path.dirname(os.path.abspath(__file__))
HOST = __default_host__
client = JinaDClient(host=HOST, port=8000)


@contextmanager
def RemoteFlow(workspace_id) -> Response:
    flow_id = client.flows.create(
        workspace_id=workspace_id, filename='flow_cache_validator.yml'
    )
    args = client.flows.get(flow_id)['arguments']['object']['arguments']
    yield Client(host=HOST, port=args['port_expose'], protocol=args['protocol']).post(
        on='/', inputs=[Document()], show_progress=True, return_results=True
    )
    assert client.flows.delete(flow_id)


def test_cache_validate_remote_flow():
    """
    This test validates that files (e.g.- pre-trained model) downloaded in an Executor
    in a remote Flow should be available to be accessed during the 2nd time an
    Executor/Flow tries accessing it.
    """
    workspace_id = client.workspaces.create(paths=[cur_dir])

    with RemoteFlow(workspace_id) as response:
        # 1st Flow in remote workspace should download the file.
        # hence `exists` should be False
        assert not response[0].data.docs[0].tags['exists']

    with RemoteFlow(workspace_id) as response:
        # 2nd Flow in remote workspace should be able to access the file.
        # hence `exists` should be True.
        assert response[0].data.docs[0].tags['exists']

    new_workspace_id = client.workspaces.create(
        paths=[
            os.path.join(cur_dir, 'cache_validator.py'),
            os.path.join(cur_dir, 'flow_cache_validator.yml'),
        ]
    )

    with RemoteFlow(new_workspace_id) as response:
        # 1st Flow in a new workspace shouldn't be able to access the file.
        # hence `exists` should be False
        assert not response[0].data.docs[0].tags['exists']


def test_cache_validate_remote_executor():
    from .cache_validator import CacheValidator

    workspace_id = random_identity()
    # 1st Executor in remote workspace should download the file.
    f = Flow().add(
        uses=CacheValidator,
        host='localhost:8000',
        py_modules='cache_validator.py',
        upload_files=cur_dir,
        workspace_id=workspace_id,
    )
    with f:
        response = f.post(
            on='/', inputs=[Document()], show_progress=True, return_results=True
        )
        assert not response[0].data.docs[0].tags['exists']

    # 2nd Executor in remote workspace should be able to access the file.
    f = Flow().add(
        uses=CacheValidator,
        host='localhost:8000',
        py_modules='cache_validator.py',
        upload_files=cur_dir,
        workspace_id=workspace_id,
    )
    with f:
        response = f.post(
            on='/', inputs=[Document()], show_progress=True, return_results=True
        )
        assert response[0].data.docs[0].tags['exists']
