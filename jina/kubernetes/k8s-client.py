import requests

ip = 'x.x.x.x'
host = 'http://{ip}:8080'
resp = requests.post(f'{host}/index', json={'data': [{'text': 'hello jina'}]})
print('first resp', resp.text)
