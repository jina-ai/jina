import os
from pathlib import Path

from jina import Flow
from jina.parsers.helloworld import set_hw_parser

if __name__ == '__main__':
    from helper import (
        print_result,
        write_html,
        download_data,
        index_generator,
        query_generator,
    )
    from my_executors import MyEncoder, MyIndexer, MyEvaluator
else:
    from .helper import (
        print_result,
        write_html,
        download_data,
        index_generator,
        query_generator,
    )
    from .my_executors import MyEncoder, MyIndexer, MyEvaluator

cur_dir = os.path.dirname(os.path.abspath(__file__))


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

    # now comes the real work
    # load index flow from a YAML file
    f = (
        Flow()
        .add(uses=MyEncoder, replicas=2)
        .add(uses=MyIndexer, workspace=args.workdir)
        .add(uses=MyEvaluator)
    )

    # run it!
    with f:
        f.index(
            index_generator(num_docs=targets['index']['data'].shape[0], target=targets),
            show_progress=True,
        )

        f.post(
            '/eval',
            query_generator(
                num_docs=args.num_query, target=targets, with_groundtruth=True
            ),
            shuffle=True,
            on_done=print_result,
            parameters={'top_k': args.top_k},
            show_progress=True,
        )

        # write result to html
        write_html(os.path.join(args.workdir, 'demo.html'))


if __name__ == '__main__':
    args = set_hw_parser().parse_args()
    hello_world(args)
