__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os
from pathlib import Path

from pkg_resources import resource_filename

from .components import *
from .helper import write_png, input_fn, print_result, write_html, download_data
from ..flow import Flow
from ..helper import countdown, colored


def hello_world(args):
    """The hello world of Jina. Use it via CLI :command:`jina hello-world`.

    It downloads Fashion-MNIST dataset and indexes 50,000 images via Jina search framework.
    The index is stored into 4 *shards*. We then randomly sample 128 unseen images as *Queries*,
    ask Jina to retrieve relevant results.

    More options can be found in :command:`jina hello-world --help`
    """
    Path(args.workdir).mkdir(parents=True, exist_ok=True)

    targets = {
        'index': {
            'url': args.index_data_url,
            'filename': os.path.join(args.workdir, 'index-original')
        },
        'query': {
            'url': args.query_data_url,
            'filename': os.path.join(args.workdir, 'query-original')
        }
    }

    download_data(targets)

    os.environ['RESOURCE_DIR'] = resource_filename('jina', 'resources')
    os.environ['SHARDS'] = str(args.shards)
    os.environ['REPLICAS'] = str(args.replicas)
    os.environ['HW_WORKDIR'] = args.workdir
    os.environ['WITH_LOGSERVER'] = str(args.logserver)
    os.environ['JINA_ARRAY_QUANT'] = 'fp16'

    f = Flow.load_config(args.index_yaml_path)
    with f:
        f.index(input_fn(targets['index']['filename']), batch_size=args.index_batch_size)

    countdown(8, reason=colored('behold! im going to switch to query mode', 'cyan',
                                attrs=['underline', 'bold', 'reverse']))

    f = Flow.load_config(args.query_yaml_path)
    with f:
        f.search(input_fn(targets['query']['filename'], index=False, num_doc=args.num_query),
                 output_fn=print_result, top_k=args.top_k, batch_size=args.query_batch_size)

    html_path = os.path.join(args.workdir, 'hello-world.html')
    write_html(html_path)
