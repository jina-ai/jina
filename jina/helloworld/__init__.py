import os
from pathlib import Path

from pkg_resources import resource_filename

from .components import *
from .helper import write_png, input_fn, print_result, write_html, download_data
from ..flow import Flow
from ..helper import countdown, colored


def hello_world(args):
    """The hello world of Jina. Use it via CLI :command:`jina hello-world`

    It downloads Fashion-MNIST dataset and indexes 50,000 images via Jina search framework.
    The index is stored into 4 *shards*. We then randomly sample 128 unseen images as *Queries*,
    ask Jina to retrieve relevant results.

    More options can be found in :command:`jina hello-world --help`
    """
    Path(args.workdir).mkdir(parents=True, exist_ok=True)

    urls = [args.index_data_url, args.query_data_url]
    targets = [os.path.join(args.workdir, 'index-original'), os.path.join(args.workdir, 'query-original')]
    download_data(targets, urls)

    os.environ['RESOURCE_DIR'] = resource_filename('jina', 'resources')
    os.environ['SHARDS'] = str(args.shards)
    os.environ['REPLICAS'] = str(args.replicas)
    os.environ['HW_WORKDIR'] = args.workdir

    f = Flow().load_config(resource_filename('jina', '/'.join(('resources', 'helloworld.flow.index.yml'))))
    with f.build() as fl:
        fl.index(raw_bytes=input_fn(targets[0]), batch_size=1024)

    countdown(8, reason=colored('behold! im going to switch to query mode', color='yellow', attrs='bold'))

    f = Flow().load_config(resource_filename('jina', '/'.join(('resources', 'helloworld.flow.query.yml'))))
    with f.build() as fl:
        fl.search(raw_bytes=input_fn(targets[1], index=False, num_doc=128),
                  callback=print_result, top_k=args.top_k, batch_size=32)

    html_path = os.path.join(args.workdir, 'hello-world.html')
    write_html(html_path)
