import os
import json
import time

from daemon.helper import get_workspace_path
from daemon.models import DaemonID
from daemon.models.containers import ContainerArguments

from daemon.models import ContainerItem
from daemon.models.containers import ContainerMetadata
from jina import Flow

log_content = """
{"host":"ubuntu","process":"32539","type":"INFO","name":"encode1","uptime":"20210124215151","context":"encode1","workspace_path":"/tmp/jinad/32aa7734-fbb8-4e7a-9f76-46221b512648","log_id":"16ef0bd7-e534-42e7-9076-87a3f585933c","message":"starting jina.peapods.runtimes.worker.WorkerRuntime..."}
{"host":"ubuntu","process":"32539","type":"INFO","name":"encode1","uptime":"20210124215151","context":"encode1/WorkerRuntime","workspace_path":"/tmp/jinad/32aa7734-fbb8-4e7a-9f76-46221b512648","log_id":"16ef0bd7-e534-42e7-9076-87a3f585933c","message":"input \u001B[33mtcp://0.0.0.0:45319\u001B[0m (PULL_BIND) output \u001B[33mtcp://0.0.0.0:59229\u001B[0m (PUSH_CONNECT) control over \u001B[33mtcp://0.0.0.0:49571\u001B[0m (PAIR_BIND)"}
{"host":"ubuntu","process":"31612","type":"SUCCESS","name":"encode1","uptime":"20210124215151","context":"encode1","workspace_path":"/tmp/jinad/32aa7734-fbb8-4e7a-9f76-46221b512648","log_id":"16ef0bd7-e534-42e7-9076-87a3f585933c","message":"ready and listening"}
{"host":"ubuntu","process":"32546","type":"INFO","name":"encode2","uptime":"20210124215151","context":"encode2","workspace_path":"/tmp/jinad/32aa7734-fbb8-4e7a-9f76-46221b512648","log_id":"16ef0bd7-e534-42e7-9076-87a3f585933c","message":"starting jina.peapods.runtimes.worker.WorkerRuntime..."}
"""

workspace_id = DaemonID('jworkspace')
flow_id = DaemonID('jflow')
nonexisting_id = DaemonID('jflow')


def _write_to_logfile(content, append=False):
    with open(
        get_workspace_path(workspace_id, 'logs', flow_id, 'logging.log'),
        'a' if append else 'w+',
    ) as f:
        f.writelines(content)


def _write_to_workspace_logfile(content, append=False):
    with open(
        get_workspace_path(workspace_id, 'logging.log'),
        'a' if append else 'w+',
    ) as f:
        f.writelines(content)


def _create_flow():
    from daemon.stores import flow_store

    flow_store[flow_id] = ContainerItem(
        metadata=ContainerMetadata(
            container_id='container_id',
            container_name='container_name',
            image_id='image_id',
            network='',
            ports={},
            rest_api_uri='',
            uri="",
        ),
        arguments=ContainerArguments(entrypoint='entrypoint', object=Flow()),
        workspace_id=workspace_id,
    )


def setup_module():
    print('setup', get_workspace_path(workspace_id, flow_id))
    _create_flow()
    os.makedirs(get_workspace_path(workspace_id, 'logs', flow_id), exist_ok=True)
    _write_to_logfile(log_content)
    _write_to_workspace_logfile(log_content)


def test_logs_invalid_flow(fastapi_client):
    response = fastapi_client.get(f'/logs/{nonexisting_id}')
    assert response.status_code == 404


def test_logs_correct_log(fastapi_client):

    response = fastapi_client.get(f'/logs/{flow_id}')
    assert response.status_code == 200
    assert response.text == log_content
