from multiprocessing import Pool

import numpy as np
import requests
import time

from jina.kubernetes import kubernetes_tools

kubernetes_tools.get_pod_logs("search-flow")

time.sleep(2)
input("Press Enter to start the requests...")

# ip = '34.141.109.41'
ip = '127.0.0.1:8081'
host = f'http://{ip}'


# search flow
data = [{'embedding': np.ones((512,)).tolist()} for _ in range(1)]


def make_request(current):
    resp = requests.post(f'{host}/search', json={'data': data})
    print(f"Len response matches: {len(resp.json()['data']['docs'][0]['matches'])}")
    print(f'{current} resp', resp.status_code)#, resp.json())


for i in range(10):
    print('request: ', i)
    make_request(i)

# with Pool(10) as p:
#     p.map(make_request, range(10))

# while True:
#     for i in range(1):
#         print('request num', i)
#         make_request(i)
#         time.sleep(1)
#     time.sleep(2000)

