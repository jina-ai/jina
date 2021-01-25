__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os
from pathlib import Path

from pkg_resources import resource_filename

from .components import *
from .helper import print_result, write_html, download_data, \
    index_generator, query_generator
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
        'index-labels': {
            'url': args.index_labels_url,
            'filename': os.path.join(args.workdir, 'index-labels')
        },
        'query-labels': {
            'url': args.query_labels_url,
            'filename': os.path.join(args.workdir, 'query-labels')
        },
        'index': {
            'url': args.index_data_url,
            'filename': os.path.join(args.workdir, 'index-original')
        },
        'query': {
            'url': args.query_data_url,
            'filename': os.path.join(args.workdir, 'query-original')
        }
    }

    # download the data
    download_data(targets, args.download_proxy)

    # this envs are referred in index and query flow YAMLs
    os.environ['RESOURCE_DIR'] = resource_filename('jina', 'resources')
    os.environ['SHARDS'] = str(args.shards)
    os.environ['PARALLEL'] = str(args.parallel)
    os.environ['HW_WORKDIR'] = args.workdir

    # reduce the network load by using `fp16`, or even `uint8`
    os.environ['JINA_ARRAY_QUANT'] = 'fp16'

    # now comes the real work
    # load index flow from a YAML file
    f = Flow.load_config(args.uses_index)

    # run it!
    with f:
        f.index(index_generator(num_docs=targets['index']['data'].shape[0], target=targets),
                request_size=args.index_request_size)

    # wait for couple of seconds
    countdown(8, reason=colored('behold! im going to switch to query mode', 'cyan',
                                attrs=['underline', 'bold', 'reverse']))

    # now load query flow from another YAML file
    f = Flow.load_config(args.uses_query)
    # run it!
    with f:
        f.search(query_generator(num_docs=args.num_query, target=targets, with_groundtruth=True),
                 shuffle=True,
                 on_done=print_result,
                 request_size=args.query_request_size,
                 top_k=args.top_k)

    # write result to html
    write_html(os.path.join(args.workdir, 'hello-world.html'))
