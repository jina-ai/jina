import time

from jina.flow import Flow


def test_simple_config():
    with Flow().add(name='pod1', replicas=2, parallel=2, port_in=5100, port_out=5200) as flow:
        print('test')


def test_port_configuration():
    def get_outer_ports(pod):
        if not 'replicas' in pod.args or int(pod.args.replicas) == 1:
            assert pod.replicas_args['tail'] is None
            assert pod.replicas_args['head'] is None
            replica = pod.replicas_args['replicas'][0] # there is only one
            return replica.port_in, replica.port_out
        else:
            assert pod.args.replicas == len(pod.replicas_args['replicas'])
            assert pod.args.replicas == len(pod.replica_list) - 2  # head and tail pea
            assert pod.args.parallel == len(pod.replica_list[0].peas_args['peas'])
            return pod.replicas_args['head'].port_in, pod.replicas_args['tail'].port_out

    def validate_ports_pods(pods):
        for i in range(len(pods) - 1):
            _, port_out = get_outer_ports(pods[i])
            port_in_next, _ = get_outer_ports(pods[i + 1])
            assert port_out == port_in_next

    def validate_ports_replica(replica, pod_head_port_out, pod_tail_port_in, parallel):
        assert pod_head_port_out == replica.args.port_in
        assert replica.args.port_out == pod_tail_port_in
        peas_args = replica.peas_args
        peas = peas_args['peas']
        if parallel == 1: #TODO handle parallel == 1
            pass
            # assert len(peas) == 1
            # assert peas[f'{replica.args.name}/1'].port_in == pod_head_port_out
            # assert peas[f'{replica.args.name}/1'].port_out == pod_tail_port_in
        else:
            shard_head = peas_args['head']
            shard_tail = peas_args['tail']
            assert replica.args.port_in == shard_head.port_in
            assert replica.args.port_out == shard_tail.port_out
            for pea in peas:
                assert shard_head.port_out == pea.port_in
                assert pea.port_out == shard_tail.port_in


    with Flow().add(name='pod1', replicas=2, parallel=3).add(
        name='pod2', replicas=3, parallel=1
    ) as flow:
        pods = flow._pod_nodes
        validate_ports_pods(
            [pods['gateway'], pods['pod1'], pods['pod2'], pods['gateway']]
        )
        for pod_name, pod in pods.items():
            if pod_name == 'gateway':
                continue
            pod_head_out = pod.head_args.port_out
            pod_tail_in = pod.tail_args.port_in
            # replica_head_out = pod.replicas_args['head'].port_out, # equals
            # replica_tail_in = pod.replicas_args['tail'].port_in, # equals


            for replica in pod.replica_list: # TODO handle replicas == 1 case
                if not ('head' in replica.name or 'tail' in replica.name):
                    validate_ports_replica(
                        replica,
                        pod_head_out,
                        pod_tail_in,
                        getattr(pod.args, 'parallel', 1)
                    )
        assert pod


def test_use_before_use_after():
    pass

def test_gateway():
    pass


def test_experimental_pod_update():
    """
    1. Create 3 pods pod1, pod2, pod3.
    2. Create a 4th pod new_pod2.
    3. Send 5 SearchRequests. They are going to pod2.
    4. Send a ReconnectPodRequest to the tail pea of pod1, to reconfigure the port_out to new_pod2.
    5. Send 5 SearchRequests. They are going to new_pod2.

    You can now search in the log for '### search request' and find:
    - 5 request to pod2/tail
    - 5 request to new_pod2/tail
    """

    def callback(resp):
        print(resp)

    with Flow().add(
        name='pod1',
        parallel=2,
        port_in=51000,
        port_out=52000,  # <-- getting changed to 54000
    ).add(
        name='pod2',  # <-- getting removed
        parallel=2,
        port_in=52000,
        port_out=53000,
        ########### This pod will be added ###########
        # ).add(
        #     name='new_pod2', # <-- new pod will be created. The name is just different for illustration purpose
        #     parallel=2,
        #     port_in=54000, # <-- has a different port_in
        #     port_out=53000,
        ##############################################
    ).add(
        name='pod3',
        parallel=2,
        port_in=53000,
    ) as flow:
        # create new pod asynchronously. Can take a lot of time.....
        flow.update_pod('pod2')

        # search requests on the old peas
        for i in range(5):
            flow.search('my_text', on_done=callback)
            time.sleep(1)

        # reconnect
        print('### second pod connecting')
        start_time = time.time()
        # switch traffic to new pod. Blocking request, but it is super fast since the new pod is there already.
        flow.reconnect_pod('pod1')
        print(
            '### finished - second pod connected. Took ',
            time.time() - start_time,
            'seconds',
        )

        # search requests on the new peas
        for i in range(5):
            flow.search('my_text', on_done=callback)
            time.sleep(1)
