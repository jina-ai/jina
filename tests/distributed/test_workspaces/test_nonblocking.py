import os
from threading import Thread, Event

import requests

from ..helpers import (
    create_workspace,
    delete_workspace,
    wait_for_workspace,
    create_flow,
    delete_flow,
)


cur_dir = os.path.dirname(os.path.abspath(__file__))

CLOUD_HOST = 'localhost:8000'  # consider it as the staged version
event = Event()
success = 0
failure = 0


def get_flows():
    global success, failure
    while not event.is_set():
        try:
            r = requests.get(f'http://{CLOUD_HOST}/flows', timeout=1)
            if r.status_code != 200:
                failure += 1
            else:
                success += 1
        except Exception:
            failure += 1
            continue


def test_nonblocking_server():
    workspace_id = create_workspace(
        dirpath=os.path.join(cur_dir, 'delayed_flow'),
    )
    assert wait_for_workspace(workspace_id)
    t = Thread(target=get_flows)
    t.start()
    flow_id = create_flow(workspace_id=workspace_id, filename='delayed_flow.yml')
    event.set()
    t.join()
    delete_flow(flow_id)
    assert success > 0, f'#success is {success} (expected >0)'
    assert failure == 0, f'#failure is {failure} (expected =0)'
    delete_workspace(workspace_id)
