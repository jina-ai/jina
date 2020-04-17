import os
import urllib.request
import webbrowser
from pathlib import Path

import numpy as np
from pkg_resources import resource_filename

from .helper import write_png, input_fn, print_result, write_html
from ..clients.python import ProgressBar
from ..executors.crafters import BaseSegmenter, BaseDocCrafter
from ..executors.encoders import BaseImageEncoder
from ..flow import Flow
from ..helper import countdown, colored
from ..logging import default_logger


class MyDocCrafter(BaseDocCrafter):
    def craft(self, raw_bytes, *args, **kwargs):
        doc = np.frombuffer(raw_bytes, dtype=np.uint8)
        return dict(meta_info=write_png(doc))


class MySegmenter(BaseSegmenter):
    def craft(self, raw_bytes, doc_id, *args, **kwargs):
        return [dict(blob=np.frombuffer(raw_bytes, dtype=np.uint8))]


class MyEncoder(BaseImageEncoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # generate a random orthogonal matrix
        H = np.random.rand(784, 64)
        u, s, vh = np.linalg.svd(H, full_matrices=False)
        self.oth_mat = u @ vh
        self.touch()

    def encode(self, data: 'np.ndarray', *args, **kwargs):
        # reduce dimension to 50 by random orthogonal projection
        return (data.reshape([-1, 784]) / 255) @ self.oth_mat


def hello_world(args):
    Path(args.workdir).mkdir(parents=True, exist_ok=True)
    urls = [args.index_data_url, args.query_data_url]

    targets = [os.path.join(args.workdir, 'index-original'), os.path.join(args.workdir, 'query-original')]

    with ProgressBar(task_name='download fashion-mnist') as t:
        for f, u in zip(targets, urls):
            if not os.path.exists(f):
                urllib.request.urlretrieve(u, f, reporthook=lambda *x: t.update(1))

    os.environ['RESOURCE_DIR'] = resource_filename('jina', 'resources')
    os.environ['SHARDS'] = str(args.shards)
    os.environ['REPLICAS'] = str(args.replicas)
    os.environ['HW_WORKDIR'] = args.workdir

    f = Flow().load_config(resource_filename('jina', '/'.join(('resources', 'helloworld.flow.index.yml'))))

    with f.build() as fl:
        fl.index(raw_bytes=input_fn(targets[0]), batch_size=1024)

    countdown(5, reason=colored('behold! im going to switch to query mode', color='green'))
    f = Flow().load_config(resource_filename('jina', '/'.join(('resources', 'helloworld.flow.query.yml'))))

    with f.build() as fl:
        fl.search(raw_bytes=input_fn(targets[1], index=False, num_doc=128),
                  callback=print_result, top_k=args.top_k, batch_size=32)

    html_path = os.path.join(args.workdir, 'hello-world.html')
    write_html(html_path)
    url_html_path = 'file://' + os.path.abspath(html_path)
    try:
        webbrowser.open(url_html_path, new=2)
    except:
        pass
    finally:
        default_logger.success(f'You should see a "hello-world.html" opened in your browser, '
                               f'if not you may open {url_html_path} manually')
