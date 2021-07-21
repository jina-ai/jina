import requests
import time

ip = 'x.x.x.x'
host = f'http://{ip}'
for _ in range(200):
    resp = requests.post(f'{host}/index', json={'data': [{'text': 'hello jina'}]})
    print('first resp', resp.text)
    time.sleep(0.5)
