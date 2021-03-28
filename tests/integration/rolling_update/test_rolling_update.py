import os
import time

import pytest

from jina import Document
from jina.flow import Flow


def test_simple_run():
    flow = Flow().add(
        name='pod1',
        replicas=2,
        parallel=3,
        port_in=5100,
        port_out=5200,  # TODO always needs to be any for replicas and all for shards
    )
    # TODO replica plot
    # flow.plot(output=os.path.join('flow2.jpg'), copy_flow=True)
    with flow:
        flow.index('documents before rolling update')
        print('#### before update ')
        # TODO test index request if it is sent only once or more often
        # TODO check original implementation
        # TODO check where ide request is sent
        flow.rolling_update('pod1')
        print('# index while roling update')
        flow.index('documents after rolling update')
        print('# terminate flow')


def test_async_run():
    flow = Flow().add(
        name='pod1',
        replicas=2,
        parallel=3,
        port_in=5100,
        port_out=5200,  # TODO always needs to be any for replicas and all for shards
    )
    with flow:
        for i in range(5):
            flow.index(Document(text='documents before rolling update'))
            time.sleep(1)
        print('#### before update ')
        flow.rolling_update_async('pod1')
        print('# index while roling update')
        for i in range(40):
            flow.index(Document(text='documents after rolling update'))
            time.sleep(0.5)
        print('# terminate flow')
    print('remove regex from log: "^[^#].*$\\n"')  # ^[^#].*$\n


@pytest.mark.parametrize(
    'replicas_and_parallel',
    (
        # ((1, 1),),
        # ((1, 2),),
        # ((2, 1),),
        # ((2, 3),),
        ((2, 1), (3, 4), (1, 2), (1, 1), (2, 2)),
    ),
)
def test_port_configuration(replicas_and_parallel):
    def get_outer_ports(pod):
        if not 'replicas' in pod.args or int(pod.args.replicas) == 1:
            assert pod.replicas_args['tail'] is None
            assert pod.replicas_args['head'] is None
            assert len(pod.replica_list) == 1
            assert len(pod.peas) == 0
            replica = pod.replicas_args['replicas'][0]  # there is only one
            return replica.port_in, replica.port_out
        else:
            assert pod.args.replicas == len(pod.replicas_args['replicas'])
            assert pod.args.replicas == len(pod.replica_list)
            assert len(pod.peas) == 2
            assert pod.args.parallel == len(pod.replica_list[0].peas_args['peas'])
            return pod.replicas_args['head'].port_in, pod.replicas_args['tail'].port_out

    def validate_ports_pods(pods):
        for i in range(len(pods) - 1):
            _, port_out = get_outer_ports(pods[i])
            port_in_next, _ = get_outer_ports(pods[i + 1])
            assert port_out == port_in_next

    def validate_ports_replica(replica, replica_port_in, replica_port_out, parallel):
        assert replica_port_in == replica.args.port_in
        assert replica.args.port_out == replica_port_out
        peas_args = replica.peas_args
        peas = peas_args['peas']
        assert len(peas) == parallel
        if parallel == 1:
            assert peas_args['head'] is None
            assert peas_args['tail'] is None
            assert peas[0].port_in == replica_port_in
            assert peas[0].port_out == replica_port_out
        else:
            shard_head = peas_args['head']
            shard_tail = peas_args['tail']
            assert replica.args.port_in == shard_head.port_in
            assert replica.args.port_out == shard_tail.port_out
            for pea in peas:
                assert shard_head.port_out == pea.port_in
                assert pea.port_out == shard_tail.port_in

    flow = Flow()
    # flow.plot() # TODO crashes for some reason when copy_flow=False
    flow.plot(output=os.path.join('flow.svg'), copy_flow=True)
    for i, (replicas, parallel) in enumerate(replicas_and_parallel):
        flow.add(
            name=f'pod{i}',
            replicas=replicas,
            parallel=parallel,
            # TODO create ticket for port_in port_out inconsistency. It is not possible to only set a custom port out
            # instead of configuring port_in and port out we should just configure the communication ports once
            port_in=f'51{i}00',  # info: needs to be set in this test since the test is asserting pod args with pod tail args
            port_out=f'51{i+1}00',  # outside this test, it don't have to be set
            copy_flow=False,
        )
    print('port assertion in configuration')

    with flow:
        pods = flow._pod_nodes
        validate_ports_pods(
            [pods['gateway']]
            + [pods[f'pod{i}'] for i in range(len(replicas_and_parallel))]
            + [pods['gateway']]
        )
        for pod_name, pod in pods.items():
            if pod_name == 'gateway':
                continue
            if pod.args.replicas == 1:
                assert len(pod.replica_list) == 1
                replica_port_in = pod.args.port_in
                replica_port_out = pod.args.port_out
            else:
                replica_port_in = pod.head_args.port_out
                replica_port_out = pod.tail_args.port_in
            # replica_head_out = pod.replicas_args['head'].port_out, # equals
            # replica_tail_in = pod.replicas_args['tail'].port_in, # equals

            for pea in pod.peas:
                if 'head' in pea.name:
                    assert pea.args.port_in == pod.args.port_in
                    assert pea.args.port_out == replica_port_in
                if 'tail' in pea.name:
                    assert pea.args.port_in == replica_port_out
                    assert pea.args.port_out == pod.args.port_out
            for replica in pod.replica_list:
                validate_ports_replica(
                    replica,
                    replica_port_in,
                    replica_port_out,
                    getattr(pod.args, 'parallel', 1),
                )

        assert pod


def test_use_before_use_after():
    pass


def test_gateway():
    pass


def test_flow_plot():
    pass


def test_workspace_configuration():
    pass
