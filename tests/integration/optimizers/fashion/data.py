import gzip
import numpy as np
import os

import urllib.request
from pathlib import Path


def load_mnist(path):
    with gzip.open(path, 'rb') as fp:
        return np.frombuffer(fp.read(), dtype=np.uint8, offset=16).reshape([-1, 784])


def load_labels(path):
    with gzip.open(path, 'rb') as fp:
        return np.frombuffer(fp.read(), dtype=np.uint8, offset=8).reshape([-1, 1])


def download_data(target, download_proxy=None):
    opener = urllib.request.build_opener()
    if download_proxy:
        proxy = urllib.request.ProxyHandler({'http': download_proxy, 'https': download_proxy})
        opener.add_handler(proxy)
    urllib.request.install_opener(opener)
    print('Downloading fashion-mnist dataset...')
    for k, v in target.items():
        if not os.path.exists(v['filename']):
            urllib.request.urlretrieve(v['url'], v['filename'])
        if k == 'index-labels' or k == 'query-labels':
            v['data'] = load_labels(v['filename'])
        if k == 'index' or k == 'query':
            v['data'] = load_mnist(v['filename'])


def get_data(data_directory):
    Path(data_directory).mkdir(parents=True, exist_ok=True)
    targets = {
        'index-labels': {
            'url': 'http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/train-labels-idx1-ubyte.gz',
            'filename': os.path.join(data_directory, 'index-labels'),
        },
        'query-labels': {
            'url': 'http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/t10k-labels-idx1-ubyte.gz',
            'filename': os.path.join(data_directory, 'query-labels'),
        },
        'index': {
            'url': 'http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/train-images-idx3-ubyte.gz',
            'filename': os.path.join(data_directory, 'index'),
        },
        'query': {
            'url': 'http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/t10k-images-idx3-ubyte.gz',
            'filename': os.path.join(data_directory, 'query'),
        },
    }

    download_data(targets)
    return targets

