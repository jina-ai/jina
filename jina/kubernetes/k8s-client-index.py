from multiprocessing import Pool

import requests
import time

from jina.kubernetes import kubernetes_tools

# kubernetes_tools.get_pod_logs("search-flow")
kubernetes_tools.get_pod_logs("index-flow")

time.sleep(2)
input("Press Enter to start the requests...")

ip = '34.141.109.41'
ip = '127.0.0.1:8080'
host = f'http://{ip}'

# index
import requests
import time


# ip = '34.136.238.119'
# ip = 'localhost:8080'
# host = f'http://{ip}'



# yields some sample data
import json
from typing import Generator

from jina import Document, DocumentArray

DATA_FILE = 'data/products.json'


def product_docs_generator() -> Generator[Document, None, None]:
    data = [
        {
            "name": f"Gucci Handbag {i}",
            "description": "Black handbag from Gucci with golden decorations.",
            "uri": "https://media.gucci.com/style/DarkGray_Center_0_0_1200x1200/1538487908/474575_DTD1T_1000_001_100_0023_Light-GG-Marmont-matelass-mini-bag.jpg"
        }
        for i in range(100)
    ]

    for product in data:
        doc = Document()
        doc.tags.update(product)
        yield doc

docs =  [doc.dict()  for doc in product_docs_generator()]
resp = requests.post(f'{host}/index', json={'data': docs})
print(resp)

















# # search flow
# data = [{'text': 'hello jina'} for _ in range(1)]
#
#
# def make_request(current):
#     resp = requests.post(f'{host}/search', json={'data': data})
#     print('resp', resp.status_code, resp.json())
#
#
# # with Pool(10) as p:
# #     p.map(make_request, range(10))
#
# while True:
#     for i in range(1):
#         print('request num', i)
#         make_request(i)
#         time.sleep(1)
#     time.sleep(2000)
