import os
import time

import pytest

from jina.flow import Flow


def test_simple_run():
    flow = Flow().add(
        name='pod1', replicas=2, parallel=3, port_in=5100, port_out=5200,  # TODO always needs to be any for replicas and all for shards
    )
    # TODO replica plot
    # flow.plot(output=os.path.join('flow2.jpg'), copy_flow=True)
    with flow:
        flow.index('test document')
        print('#### before update ')
        time.sleep(1)
        # TODO test index request if it is sent only once or more often
        # TODO check original implementation
        # TODO check where ide request is sent
        flow.rolling_update('pod1')
        # print('#### after update ')
        # time.sleep(10000)
        flow.index('test2')


@pytest.mark.parametrize(
    'replicas_and_parallel', (
            # ((1, 1),),
            # ((1, 2),),
            # ((2, 1),),
            # ((2, 3),),
            ((2, 1), (3, 4), (1, 2), (1, 1), (2, 2)),
    ))
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
            port_in=f'51{i}00',  #info: needs to be set in this test since the test is asserting pod args with pod tail args
            port_out=f'51{i+1}00', #outside this test, it don't have to be set
            copy_flow=False
        )
    print('port assertion in configuration')

    with flow:
        pods = flow._pod_nodes
        validate_ports_pods(
            [pods['gateway']] + [pods[f'pod{i}'] for i in range(len(replicas_and_parallel))] + [pods['gateway']]
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
                    getattr(pod.args, 'parallel', 1))

        assert pod


def test_use_before_use_after():
    pass


def test_gateway():
    pass


# def test_experimental_pod_update():
#     """
#     1. Create 3 pods pod1, pod2, pod3.
#     2. Create a 4th pod new_pod2.
#     3. Send 5 SearchRequests. They are going to pod2.
#     4. Send a ReconnectPodRequest to the tail pea of pod1, to reconfigure the port_out to new_pod2.
#     5. Send 5 SearchRequests. They are going to new_pod2.
#
#     You can now search in the log for '### search request' and find:
#     - 5 request to pod2/tail
#     - 5 request to new_pod2/tail
#     """
#
#     def callback(resp):
#         print(resp)
#
#     with Flow().add(
#             name='pod1',
#             parallel=2,
#             port_in=51000,
#             port_out=52000,  # <-- getting changed to 54000
#     ).add(
#         name='pod2',  # <-- getting removed
#         parallel=2,
#         port_in=52000,
#         port_out=53000,
#         ########### This pod will be added ###########
#         # ).add(
#         #     name='new_pod2', # <-- new pod will be created. The name is just different for illustration purpose
#         #     parallel=2,
#         #     port_in=54000, # <-- has a different port_in
#         #     port_out=53000,
#         ##############################################
#     ).add(
#         name='pod3',
#         parallel=2,
#         port_in=53000,
#     ) as flow:
#         # create new pod asynchronously. Can take a lot of time.....
#         flow.update_pod('pod2')
#
#         # search requests on the old peas
#         for i in range(5):
#             flow.search('my_text', on_done=callback)
#             time.sleep(1)
#
#         # reconnect
#         print('### second pod connecting')
#         start_time = time.time()
#         # switch traffic to new pod. Blocking request, but it is super fast since the new pod is there already.
#         flow.reconnect_pod('pod1')
#         print(
#             '### finished - second pod connected. Took ',
#             time.time() - start_time,
#             'seconds',
#         )
#
#         # search requests on the new peas
#         for i in range(5):
#             flow.search('my_text', on_done=callback)
#             time.sleep(1)
