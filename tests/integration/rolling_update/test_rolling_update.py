import time

from jina.flow import Flow


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

