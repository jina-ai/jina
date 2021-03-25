import time

from jina.flow import Flow



# get_replica_ports()

def test_port_configuration():
    def get_outer_ports(pod):
        if not 'replicas' in pod.args or int(pod.args.replicas) == 1:
            assert pod.replicas_args['tail'] is None
            assert pod.replicas_args['head'] is None
            replica = pod.replicas_args['replicas'][0]
            return replica.port_in, replica.port_out
        else:
            assert pod.args.replicas == len(pod.replicas_args['replicas'])
            assert pod.args.replicas == len(pod.replica_list) - 2 # head and tail pea
            assert pod.args.parallel == len(pod.replica_list[0].peas_args['peas'])
            return pod.replicas_args['head'].port_in, pod.replicas_args['tail'].port_out

    def validate_ports_pods(pods):
        for i in range(len(pods) - 1):
            _, port_out = get_outer_ports(pods[i])
            port_in_next, _ = get_outer_ports(pods[i+1])
            assert port_out == port_in_next

    def validate_ports_replica(replicas, pod_head_port_out, pod_tail_port_in, parallel):
        for replica_name, replica in replicas.items:
            peas = replica.peas

            if parallel == 1:
                peas = replica.peas
                assert len(peas) == 1
                assert peas[f'{replica_name}/1'].port_in == pod_head_port_out
                assert peas[f'{replica_name}/1'].port_out == pod_tail_port_in
            else:
                pass
                # for..

    with Flow().add(name='pod1', replicas=2, parallel=3).add(name='pod2', replicas=3, parallel=1) as flow:
        pods = flow._pod_nodes
        validate_ports_pods([pods['gateway'], pods['pod1'], pods['pod2'], pods['gateway']])
        for pod in pods:
            validate_ports_replica(pod.replicas, pod.head_pea.port_out, pod.tail_pea.port_in, pod.args['parallel'])


        assert pod

def test_use_before_use_after():
    pass

def test_experimental_pod_update():
    '''
        1. Create 3 pods pod1, pod2, pod3.
        2. Create a 4th pod new_pod2.
        3. Send 5 SearchRequests. They are going to pod2.
        4. Send a ReconnectPodRequest to the tail pea of pod1, to reconfigure the port_out to new_pod2.
        5. Send 5 SearchRequests. They are going to new_pod2.

        You can now search in the log for '### search request' and find:
        - 5 request to pod2/tail
        - 5 request to new_pod2/tail
    '''
    def callback(resp):
        print(resp)

    with Flow(
    ).add(
        name='pod1',
        parallel=2,
        port_in=51000,
        port_out=52000, # <-- getting changed to 54000
    ).add(
        name='pod2', # <-- getting removed
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
        print('### finished - second pod connected. Took ', time.time() - start_time, 'seconds')

        # search requests on the new peas
        for i in range(5):
            flow.search('my_text', on_done=callback)
            time.sleep(1)

