import os
from threading import Thread, Event

import requests

from ..helpers import (
    get_cloudhost,
    create_workspace,
    wait_for_workspace,
    delete_workspace,
    create_flow,
    delete_flow,
)


cur_dir = os.path.dirname(os.path.abspath(__file__))

HOST, PORT_EXPOSE = get_cloudhost(2)
event = Event()
success = 0
failure = 0


def get_flows():
    global success, failure
    while not event.is_set():
        try:
            r = requests.get(f'http://{HOST}:{PORT_EXPOSE}/flows', timeout=2)
            if r.status_code != 200:
                failure += 1
            else:
                success += 1
        except Exception:
            failure += 1
            continue


def test_nonblocking_server():
    workspace_id = create_workspace(
        dirpath=os.path.join(cur_dir, 'delayed_flow'), host=HOST, port=PORT_EXPOSE
    )
    assert wait_for_workspace(workspace_id=workspace_id, host=HOST, port=PORT_EXPOSE)
    t = Thread(target=get_flows)
    t.start()
    flow_id = create_flow(
        workspace_id=workspace_id,
        filename='delayed_flow.yml',
        host=HOST,
        port=PORT_EXPOSE,
    )
    event.set()
    t.join()
    delete_flow(flow_id=flow_id, host=HOST, port=PORT_EXPOSE)
    assert success > 0, f'#success is {success} (expected >0)'
    assert failure == 0, f'#failure is {failure} (expected =0)'
    delete_workspace(workspace_id=workspace_id, host=HOST, port=PORT_EXPOSE)
