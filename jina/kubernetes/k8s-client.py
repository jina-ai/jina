from multiprocessing import Pool

import requests
import time

from jina.kubernetes import kubernetes_tools



kubernetes_tools.get_pod_logs("f1")

time.sleep(2)
input("Press Enter to start the requests...")

ip = '34.141.109.41'
ip = '127.0.0.1:8080'
host = f'http://{ip}'

data = [{'text': 'hello jina'} for _ in range(1)]
def make_request(current):
    resp = requests.post(f'{host}/index', json={'data': data})
    # print('resp', resp.status_code)

with Pool(10) as p:
    p.map(make_request, range(10))

# while True:
#     for i in range(100):
#         print('request num', i)
#
#
#     time.sleep(5000)
