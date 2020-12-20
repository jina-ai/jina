__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import gzip
import os
import urllib.request
import webbrowser
import random
from collections import defaultdict

import numpy as np
from pkg_resources import resource_filename

from ..helper import colored
from ..logging import default_logger
from ..logging.profile import ProgressBar
from .. import Document

result_html = []
num_docs_evaluated = 0
evaluation_value = defaultdict(float)


def compute_mean_evaluation(resp):
    global num_docs_evaluated
    global evaluation_value
    for d in resp.search.docs:
        num_docs_evaluated += 1
        for evaluation in d.evaluations:
            evaluation_value[evaluation.op_name] += evaluation.value


def group_index_docs_by_label(targets: dict):
    targets_by_label = defaultdict(list)
    for internal_doc_id in range(len(targets['index']['data'])):
        label_int = targets['index-labels']['data'][internal_doc_id][0]
        targets_by_label[label_int].append(internal_doc_id)
    return targets_by_label


def evaluate_generator(num_docs: int, target: dict, targets_by_label: dict):
    for j in range(num_docs):
        num_data = len(target['query-labels']['data'])
        n = random.randint(0, num_data)
        label_int = target['query-labels']['data'][n][0]
        document = Document(content=(target['query']['data'][n]))
        ground_truth = Document()
        for doc_id in targets_by_label[label_int]:
            match = Document()
            match.tags['id'] = doc_id
            ground_truth.matches.append(match)
        yield document, ground_truth


def index_generator(num_docs: int, target: dict):
    for internal_doc_id in range(num_docs):
        d = Document(content=target['index']['data'][internal_doc_id])
        d.tags['id'] = internal_doc_id
        yield d


def query_generator(num_docs: int, target: dict):
    for n in range(num_docs):
        num_data = len(target['query-labels']['data'])
        n = random.randint(0, num_data)
        d = Document(content=(target['query']['data'][n]))
        yield d


def print_result(resp):
    for d in resp.search.docs:
        vi = d.uri
        result_html.append(f'<tr><td><img src="{vi}"/></td><td>')
        for kk in d.matches:
            kmi = kk.uri
            result_html.append(f'<img src="{kmi}" style="opacity:{kk.score.value}"/>')
        result_html.append('</td></tr>\n')


def write_html(html_path):
    with open(resource_filename('jina', '/'.join(('resources', 'helloworld.html'))), 'r') as fp, \
            open(html_path, 'w') as fw:
        t = fp.read()
        t = t.replace('{% RESULT %}', '\n'.join(result_html))
        precision_evaluation_percentage = evaluation_value['evaluate-Precision@5'] / num_docs_evaluated * 100.0
        recall_evaluation_percentage = evaluation_value['evaluate-Recall@5'] / num_docs_evaluated * 100.0
        t = t.replace('{% PRECISION_EVALUATION %}', '{:.2f}%'.format(precision_evaluation_percentage))
        t = t.replace('{% RECALL_EVALUATION %}', '{:.2f}%'.format(recall_evaluation_percentage))

        fw.write(t)

    url_html_path = 'file://' + os.path.abspath(html_path)

    try:
        webbrowser.open(url_html_path, new=2)
    except:
        pass  # intentional pass, browser support isn't cross-platform
    finally:
        default_logger.success(f'You should see a "hello-world.html" opened in your browser, '
                               f'if not you may open {url_html_path} manually')

    colored_url = colored('https://opensource.jina.ai', color='cyan', attrs='underline')
    default_logger.success(
        f'🤩 Intrigued? Play with "jina hello-world --help" and learn more about Jina at {colored_url}')


def download_data(targets, download_proxy=None):
    opener = urllib.request.build_opener()
    if download_proxy:
        proxy = urllib.request.ProxyHandler({'http': download_proxy, 'https': download_proxy})
        opener.add_handler(proxy)
    urllib.request.install_opener(opener)
    with ProgressBar(task_name='download fashion-mnist', batch_unit='') as t:
        for k, v in targets.items():
            if not os.path.exists(v['filename']):
                urllib.request.urlretrieve(v['url'], v['filename'], reporthook=lambda *x: t.update(1))
            if k == 'index-labels' or k == 'query-labels':
                v['data'] = load_labels(v['filename'])
            if k == 'index' or k == 'query':
                v['data'] = load_mnist(v['filename'])


def load_mnist(path):
    with gzip.open(path, 'rb') as fp:
        return np.frombuffer(fp.read(), dtype=np.uint8, offset=16).reshape([-1, 784])


def load_labels(path: str):
    with gzip.open(path, 'rb') as fp:
        return np.frombuffer(fp.read(), dtype=np.uint8, offset=8).reshape([-1, 1])
