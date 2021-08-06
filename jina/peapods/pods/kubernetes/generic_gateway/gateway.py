import base64
import sys

from jina import Flow

print('args', sys.argv)
flow_yaml_b64 = sys.argv[1]
flow_yaml = base64.b64decode(flow_yaml_b64).decode('utf8')
print('flow: \n', flow_yaml)
flow = Flow.load_config(flow_yaml)

with flow:
    print('routing table', flow._pod_nodes['gateway'].args.routing_table)
    flow.block()
