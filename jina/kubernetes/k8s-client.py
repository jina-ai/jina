
import requests
import time

from jina.kubernetes import kubernetes_tools

kubernetes_tools.get_pod_logs("f1")


ip = '34.141.109.41'
host = f'http://{ip}'
while True:
    resp = requests.post(f'{host}/index', json={'data': [{'text': 'hello jina'}]})
    # print('resp', resp.status_code)
    time.sleep(0.5)
