import os
from pathlib import Path

from jina import Flow
from jina.helper import countdown
from jina.parsers.helloworld import set_hw_parser

if __name__ == '__main__':
    from helper import (
        print_result,
        write_html,
        download_data,
        index_generator,
        query_generator,
        colored,
    )
else:
    from .helper import (
        print_result,
        write_html,
        download_data,
        index_generator,
        query_generator,
        colored,
    )

cur_dir = os.path.dirname(os.path.abspath(__file__))


def search(query_document, on_done_callback, on_fail_callback, top_k):
    with Flow.load_config('flow.yml') as f:
        f.search(
            inputs=[query_document],
            on_done=on_done_callback,
            on_fail=on_fail_callback,
            parameters={'top_k': top_k},
        )


def hello_world(args):
    """
    Runs Jina's Hello World.

    Usage:
        Use it via CLI :command:`jina hello-world`.

    Description:
        It downloads Fashion-MNIST dataset and :term:`Indexer<indexes>` 50,000 images.
        The index is stored into 4 *shards*. It randomly samples 128 unseen images as :term:`Queries<Searching>`
        Results are shown in a webpage.

    More options can be found in :command:`jina hello-world --help`

    :param args: Argparse object
    """

    Path(args.workdir).mkdir(parents=True, exist_ok=True)

    targets = {
        'index-labels': {
            'url': args.index_labels_url,
            'filename': os.path.join(args.workdir, 'index-labels'),
        },
        'query-labels': {
            'url': args.query_labels_url,
            'filename': os.path.join(args.workdir, 'query-labels'),
        },
        'index': {
            'url': args.index_data_url,
            'filename': os.path.join(args.workdir, 'index-original'),
        },
        'query': {
            'url': args.query_data_url,
            'filename': os.path.join(args.workdir, 'query-original'),
        },
    }

    # download the data
    download_data(targets, args.download_proxy)

    # reduce the network load by using `fp16`, or even `uint8`
    os.environ['JINA_ARRAY_QUANT'] = 'fp16'
    os.environ['HW_WORKDIR'] = args.workdir

    # now comes the real work
    # load index flow from a YAML file
    f = Flow.load_config('flow.yml')

    # run it!
    with f:
        f.index(
            index_generator(num_docs=targets['index']['data'].shape[0], target=targets),
            request_size=args.index_request_size,
        )

        # wait for couple of seconds
        countdown(
            3,
            reason=colored(
                'behold! im going to switch to query mode',
                'cyan',
                attrs=['underline', 'bold', 'reverse'],
            ),
        )

        f.search(
            query_generator(
                num_docs=args.num_query, target=targets, with_groundtruth=True
            ),
            shuffle=True,
            on_done=print_result,
            request_size=args.query_request_size,
            parameters={'top_k': args.top_k},
        )

    # write result to html
    write_html(os.path.join(args.workdir, 'demo.html'))


if __name__ == '__main__':
    args = set_hw_parser().parse_args()
    hello_world(args)
