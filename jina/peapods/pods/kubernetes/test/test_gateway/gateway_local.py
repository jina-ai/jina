from jina import Flow

f = Flow.load_config('gateway.yaml')

with f:
    print('routing table', f._pod_nodes['gateway'].args.routing_table)
    pod = f._pod_nodes['cliptext']
    pod_args = pod.args
    peas_args = pod.peas_args
    f.block()
