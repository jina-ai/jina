import os
import json
import time
from daemon.stores.helper import get_workspace_path
from daemon.api.endpoints import logs
from daemon import jinad_args


log_content = """
{"host":"ubuntu","process":"32539","type":"INFO","name":"encode1","uptime":"20210124215151","context":"encode1","workspace_path":"/tmp/jinad/32aa7734-fbb8-4e7a-9f76-46221b512648","log_id":"16ef0bd7-e534-42e7-9076-87a3f585933c","message":"starting jina.peapods.runtimes.zmq.zed.ZEDRuntime..."}
{"host":"ubuntu","process":"32539","type":"INFO","name":"encode1","uptime":"20210124215151","context":"encode1/ZEDRuntime","workspace_path":"/tmp/jinad/32aa7734-fbb8-4e7a-9f76-46221b512648","log_id":"16ef0bd7-e534-42e7-9076-87a3f585933c","message":"input \u001B[33mtcp://0.0.0.0:45319\u001B[0m (PULL_BIND) output \u001B[33mtcp://0.0.0.0:59229\u001B[0m (PUSH_CONNECT) control over \u001B[33mtcp://0.0.0.0:49571\u001B[0m (PAIR_BIND)"}
{"host":"ubuntu","process":"31612","type":"SUCCESS","name":"encode1","uptime":"20210124215151","context":"encode1","workspace_path":"/tmp/jinad/32aa7734-fbb8-4e7a-9f76-46221b512648","log_id":"16ef0bd7-e534-42e7-9076-87a3f585933c","message":"ready and listening"}
{"host":"ubuntu","process":"32546","type":"INFO","name":"encode2","uptime":"20210124215151","context":"encode2","workspace_path":"/tmp/jinad/32aa7734-fbb8-4e7a-9f76-46221b512648","log_id":"16ef0bd7-e534-42e7-9076-87a3f585933c","message":"starting jina.peapods.runtimes.zmq.zed.ZEDRuntime..."}
"""

workspace_id = 'acd2fa50-02a6-452d-add7-ff987810c741'
flow_id = 'f0f90a3d-d2d9-4646-96d5-2560886f6ef0'
nonexisting_id = 'fff90a3d-d2d9-4646-96d5-2560886ffff0'


def _write_to_logfile(content, append=False):
    with open(
        get_workspace_path(workspace_id, flow_id, 'logging.log'),
        'a' if append else 'w+',
    ) as f:
        f.writelines(content)


def setup_module():
    print('setup', get_workspace_path(workspace_id, flow_id))
    os.makedirs(get_workspace_path(workspace_id, flow_id), exist_ok=True)
    _write_to_logfile(log_content)


def test_logs_invalid_workspace(fastapi_client):
    response = fastapi_client.get(f'/logs/{nonexisting_id}/{flow_id}')
    assert response.status_code == 404


def test_logs_invalid_flow(fastapi_client):
    response = fastapi_client.get(f'/logs/{workspace_id}/{nonexisting_id}')
    assert response.status_code == 404


def test_logs_wrong_order(fastapi_client):
    response = fastapi_client.get(f'/logs/{flow_id}/{workspace_id}')
    assert response.status_code == 404


def test_logs_correct_log(fastapi_client):
    response = fastapi_client.get(f'/logs/{workspace_id}/{flow_id}')
    assert response.status_code == 200
    assert response.text == log_content


def test_logstream_missing(fastapi_client):
    received = None
    with fastapi_client.websocket_connect(
        f'/logstream/{workspace_id}/{nonexisting_id}?timeout=3'
    ) as websocket:
        try:
            received = websocket.receive_json()
        except Exception:
            exception_raised = True
    assert received is None
    assert exception_raised


def test_logstream_valid(fastapi_client):
    line = '{"host":"test-host","process":"12034","type":"INFO","name":"Flow","uptime":"2021-04-02T20:58:10.819138","context":"Flow","workspace_path":"...","log_id":"...","message":"1 Pods (i.e. 1 Peas) are running in this Flow"}\n'
    received = None
    with fastapi_client.websocket_connect(
        f'/logstream/{workspace_id}/{flow_id}?timeout=3'
    ) as websocket:
        time.sleep(0.25)
        _write_to_logfile(line, True)
        received = websocket.receive_json()
    assert received is not None
    assert received == json.loads(line)
