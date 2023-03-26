import pytest

import jraft
from jina import Flow
from jina.helper import random_port
from jina.serve.helper import _get_workspace_from_name_and_shards


def test_stateful_restore(tmpdir):
    gateway_port = random_port()
    pod_ports = [random_port(), random_port(), random_port()]

    flow = Flow(port=gateway_port).add(
        replicas=3,
        workspace=tmpdir,
        pod_ports=pod_ports,
        stateful=True,
        raft_configuration={
            'snapshot_interval': 10,
            'snapshot_threshold': 5,
            'trailing_logs': 10,
            'LogLevel': 'INFO',
        },
    )

    with flow:
        pass

    for raft_id in range(3):
        raft_dir = _get_workspace_from_name_and_shards(
            workspace=tmpdir, name='raft', shard_id=-1
        )
        persisted_address = jraft.get_configuration(str(raft_id), raft_dir)
        assert persisted_address == f'0.0.0.0:{pod_ports[raft_id]}'
