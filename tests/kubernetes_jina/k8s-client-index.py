from multiprocessing import Pool

import requests
import time

from jina.kubernetes import kubernetes_tools

# kubernetes_tools.get_pod_logs("search-flow")
kubernetes_tools.get_pod_logs("index-flow")

time.sleep(2)
input("Press Enter to start the requests...")

ip = '127.0.0.1:8080'
host = f'http://{ip}'

import requests


from typing import Generator

from jina import Document

DATA_FILE = 'data/products.json'


def product_docs_generator() -> Generator[Document, None, None]:
    data = [
        {
            "name": f"Gucci Handbag {i+100}",
            "description": "Black handbag from Gucci with golden decorations.",
            "uri": "https://media.gucci.com/style/DarkGray_Center_0_0_1200x1200/1538487908/474575_DTD1T_1000_001_100_0023_Light-GG-Marmont-matelass-mini-bag.jpg",
        }
        for i in range(10000)
    ]

    for product in data:
        doc = Document()
        doc.tags.update(product)
        yield doc


docs = [doc.dict() for doc in product_docs_generator()]
for d in docs:
    resp = requests.post(f'{host}/index', json={'data': [d]})
    print(resp.text)
