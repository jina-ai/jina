from multiprocessing import Pool

import numpy as np
import requests
import time

from jina.clients.grpc import GRPCClient, AsyncGRPCClient
from jina.peapods.pods.kubernetes import kubernetes_tools

kubernetes_tools.get_pod_logs("search-flow")

time.sleep(2)
input("Press Enter to start the requests...")

# ip = '34.141.109.41'
ip = '127.0.0.1'
port = '8080'
host = f'http://{ip}:{port}'


# search flow
data = [{'embedding': np.ones((512,)).tolist()} for _ in range(1)]


def make_request(current):
    resp = requests.post(f'{host}/search', json={'data': data})
    print(f"Len response matches: {len(resp.json()['data']['docs'][0]['matches'])}")
    print(f'{current} resp', resp.status_code)#, resp.json())

# def make_request_gRPC(current):
#     client = GRPCClient(host=ip, port_expose=port, protocol='grpc')
#     resp = client.search(inputs=data, return_results=True)
#     print('type: ', type(resp))
#     for x in resp:
#         print(x)



for i in range(10):
    print('request: ', i)
    make_request(i)
    # make_request_gRPC(i)

# with Pool(10) as p:
#     p.map(make_request, range(10))

# while True:
#     for i in range(1):
#         print('request num', i)
#         make_request(i)
#         time.sleep(1)
#     time.sleep(2000)

