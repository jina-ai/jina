import gzip
import os
import random
import urllib.request
import webbrowser
from collections import defaultdict

import numpy as np
from docarray import Document

from jina.helper import colored
from jina.logging.predefined import default_logger
from jina.logging.profile import ProgressBar

result_html = []
top_k = 0
num_docs_evaluated = 0
evaluation_value = defaultdict(float)


def get_groundtruths(target, pseudo_match=False):
    # group doc_ids by their labels
    a = np.squeeze(target['index-labels']['data'])
    a = np.stack([a, np.arange(len(a))], axis=1)
    a = a[a[:, 0].argsort()]
    lbl_group = np.split(a[:, 1], np.unique(a[:, 0], return_index=True)[1][1:])

    # each label has one groundtruth, i.e. all docs that have the same label are considered as matches
    groundtruths = {lbl: Document(tags={'id': -1}) for lbl in range(10)}
    for lbl, doc_ids in enumerate(lbl_group):
        if not pseudo_match:
            # full-match, each doc has 6K matches
            for doc_id in doc_ids:
                match = Document()
                match.tags['id'] = int(doc_id)
                groundtruths[lbl].matches.append(match)
        else:
            # pseudo-match, each doc has only one match, but this match's id is a list of 6k elements
            match = Document()
            match.tags['id'] = doc_ids.tolist()
            groundtruths[lbl].matches.append(match)

    return groundtruths


def index_generator(num_docs: int, target: dict):
    """
    Generate the index data.

    :param num_docs: Number of documents to be indexed.
    :param target: Dictionary which stores the data paths
    :yields: index data
    """
    for internal_doc_id in range(num_docs):
        # x_blackwhite.shape is (28,28)
        x_blackwhite = 255 - target['index']['data'][internal_doc_id]
        # x_color.shape is (28,28,3)
        x_color = np.stack((x_blackwhite,) * 3, axis=-1)
        d = Document(content=x_color)
        d.tags['id'] = internal_doc_id
        yield d


def query_generator(num_docs: int, target: dict):
    """
    Generate the query data.

    :param num_docs: Number of documents to be queried
    :param target: Dictionary which stores the data paths
    :yields: query data
    """
    for _ in range(num_docs):
        num_data = len(target['query-labels']['data'])
        idx = random.randint(0, num_data - 1)
        # x_blackwhite.shape is (28,28)
        x_blackwhite = 255 - target['query']['data'][idx]
        # x_color.shape is (28,28,3)
        x_color = np.stack((x_blackwhite,) * 3, axis=-1)
        d = Document(
            content=x_color,
            tags={
                'id': -1,
                'query_label': float(target['query-labels']['data'][idx][0]),
            },
        )

        yield d


def print_result(groundtruths, resp):
    from docarray import DocumentArray

    global top_k
    global evaluation_value
    """
    Callback function to receive results.

    :param resp: returned response with data
    """
    queries = DocumentArray()
    queries.extend(resp.docs)

    gts = DocumentArray()
    for query in queries:
        gt = groundtruths[query.tags['query_label']]
        gts.append(gt)

    queries.evaluate(
        gts, metric='recall_at_k', hash_fn=lambda d: d.tags['id'], top_k=50
    )
    queries.evaluate(
        gts, metric='precision_at_k', hash_fn=lambda d: d.tags['id'], top_k=50
    )
    for query in queries:
        vi = query.uri

        result_html.append(f'<tr><td><img src="{vi}"/></td><td>')
        top_k = len(query.matches)
        for kk in query.matches:
            kmi = kk.uri
            result_html.append(
                f'<img src="{kmi}" style="opacity:{kk.scores["cosine"].value}"/>'
            )
        result_html.append('</td></tr>\n')

        # update evaluation values
        # as evaluator set to return running avg, here we can simply replace the value
        for k, evaluation in query.evaluations.items():
            evaluation_value[k] = evaluation.value


def write_html(html_path):
    """
    Method to present results in browser.

    :param html_path: path of the written html
    """

    with open(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), 'demo.html')
    ) as fp, open(html_path, 'w') as fw:
        t = fp.read()
        t = t.replace('{% RESULT %}', '\n'.join(result_html))
        t = t.replace(
            '{% PRECISION_EVALUATION %}',
            '{:.2f}%'.format(evaluation_value['precision_at_k'] * 100.0),
        )
        t = t.replace(
            '{% RECALL_EVALUATION %}',
            '{:.2f}%'.format(evaluation_value['recall_at_k'] * 100.0),
        )
        t = t.replace('{% TOP_K %}', str(top_k))
        fw.write(t)

    url_html_path = 'file://' + os.path.abspath(html_path)

    try:
        webbrowser.open(url_html_path, new=2)
    except:
        pass  # intentional pass, browser support isn't cross-platform
    finally:
        default_logger.info(
            f'You should see a "demo.html" opened in your browser, '
            f'if not you may open {url_html_path} manually'
        )

    colored_url = colored(
        'https://github.com/jina-ai/jina', color='cyan', attrs='underline'
    )
    default_logger.info(
        f'🤩 Intrigued? Play with `jina hello fashion --help` and learn more about Jina at {colored_url}'
    )


def download_data(targets, download_proxy=None, task_name='download fashion-mnist'):
    """
    Download data.

    :param targets: target path for data.
    :param download_proxy: download proxy (e.g. 'http', 'https')
    :param task_name: name of the task
    """
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    if download_proxy:
        proxy = urllib.request.ProxyHandler(
            {'http': download_proxy, 'https': download_proxy}
        )
        opener.add_handler(proxy)

    urllib.request.install_opener(opener)
    with ProgressBar(total_length=len(targets), description=task_name) as t:
        for k, v in targets.items():
            if not os.path.exists(v['filename']):
                urllib.request.urlretrieve(
                    v['url'],
                    v['filename'],
                )
                t.update()
            if k == 'index-labels' or k == 'query-labels':
                v['data'] = load_labels(v['filename'])
            if k == 'index' or k == 'query':
                v['data'] = load_mnist(v['filename'])


def load_mnist(path):
    """
    Load MNIST data

    :param path: path of data
    :return: MNIST data in np.array
    """

    with gzip.open(path, 'rb') as fp:
        return np.frombuffer(fp.read(), dtype=np.uint8, offset=16).reshape([-1, 28, 28])


def load_labels(path: str):
    """
    Load labels from path

    :param path: path of labels
    :return: labels in np.array
    """
    with gzip.open(path, 'rb') as fp:
        return np.frombuffer(fp.read(), dtype=np.uint8, offset=8).reshape([-1, 1])
