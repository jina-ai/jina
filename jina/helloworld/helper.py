__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import gzip
import os
import urllib.request
import webbrowser

import numpy as np
from pkg_resources import resource_filename

from ..clients.python import ProgressBar
from ..helper import colored
from ..logging import default_logger


def load_mnist(path):
    with gzip.open(path, 'rb') as fp:
        return np.frombuffer(fp.read(), dtype=np.uint8, offset=16).reshape([-1, 784])


def input_fn(fp, index=True, num_doc=None):
    img_data = load_mnist(fp)
    if not index:
        # shuffle for random query
        img_data = np.take(img_data, np.random.permutation(img_data.shape[0]), axis=0)
    d_id = 0
    for r in img_data:
        yield r.tobytes()
        d_id += 1
        if num_doc is not None and d_id > num_doc:
            break


result_html = []


def print_result(resp):
    for d in resp.search.docs:
        vi = d.data_uri
        result_html.append(f'<tr><td><img src="{vi}"/></td><td>')
        for kk in d.topk_results:
            kmi = kk.match_doc.data_uri
            result_html.append(f'<img src="{kmi}" style="opacity:{kk.score.value}"/>')
            # k['score']['explained'] = json.loads(kk.score.explained)
        result_html.append('</td></tr>\n')


def write_html(html_path):
    with open(resource_filename('jina', '/'.join(('resources', 'helloworld.html'))), 'r') as fp, \
            open(html_path, 'w') as fw:
        t = fp.read()
        t = t.replace('{% RESULT %}', '\n'.join(result_html))
        fw.write(t)

    url_html_path = 'file://' + os.path.abspath(html_path)

    try:
        webbrowser.open(url_html_path, new=2)
    except:
        pass
    finally:
        default_logger.success(f'You should see a "hello-world.html" opened in your browser, '
                               f'if not you may open {url_html_path} manually')

    colored_url = colored('https://opensource.jina.ai', color='cyan', attrs='underline')
    default_logger.success(
        f'🤩 Intrigued? Play with "jina hello-world --help" and learn more about Jina at {colored_url}')


def download_data(targets):
    with ProgressBar(task_name='download fashion-mnist') as t:
        for v in targets.values():
            if not os.path.exists(v['filename']):
                urllib.request.urlretrieve(v['url'], v['filename'], reporthook=lambda *x: t.update(1))
