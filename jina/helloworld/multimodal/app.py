import os
import urllib.request
import webbrowser
import zipfile
from pathlib import Path

from docarray import DocumentArray

from jina import Flow
from jina.importer import ImportExtensions
from jina.logging.predefined import default_logger
from jina.logging.profile import ProgressBar
from jina.parsers.helloworld import set_hw_multimodal_parser

cur_dir = os.path.dirname(os.path.abspath(__file__))


def hello_world(args):
    """
    Execute the multimodal example.

    :param args: arguments passed from CLI
    """
    Path(args.workdir).mkdir(parents=True, exist_ok=True)

    with ImportExtensions(
        required=True,
        help_text='this demo requires Pytorch and Transformers to be installed, '
        'if you haven\'t, please do `pip install jina[torch,transformers]`',
    ):
        import torch
        import torchvision
        import transformers

        assert [
            torch,
            transformers,
            torchvision,
        ]  #: prevent pycharm auto remove the above line

    # args.workdir = '0bae16ce-5bb2-43be-bcd4-6f1969e8068f'
    targets = {
        'people-img': {
            'url': args.index_data_url,
            'filename': os.path.join(args.workdir, 'dataset.zip'),
        }
    }

    # download the data
    if not os.path.exists(targets['people-img']['filename']):
        download_data(targets, args.download_proxy, task_name='download zip data')

    with zipfile.ZipFile(targets['people-img']['filename'], 'r') as fp:
        fp.extractall(args.workdir)

    # this envs are referred in index and query flow YAMLs
    os.environ['HW_WORKDIR'] = args.workdir
    os.environ['PY_MODULE'] = os.path.abspath(os.path.join(cur_dir, 'my_executors.py'))
    # now comes the real work
    # load index flow from a YAML file

    # index it!
    f = Flow.load_config('flow-index.yml')

    with f, open(f'{args.workdir}/people-img/meta.csv', newline='') as fp:
        f.index(inputs=DocumentArray.from_csv(fp), request_size=10, show_progress=True)
        f.post(on='/dump', target_executor='textIndexer')
        f.post(on='/dump', target_executor='imageIndexer')
        f.post(on='/dump', target_executor='keyValueIndexer')

    # search it!
    f = Flow.load_config('flow-search.yml')
    # switch to HTTP gateway
    f.protocol = 'http'
    f.port = args.port

    url_html_path = 'file://' + os.path.abspath(
        os.path.join(cur_dir, 'static/index.html')
    )
    with f:
        try:
            webbrowser.open(url_html_path, new=2)
        except:
            pass  # intentional pass, browser support isn't cross-platform
        finally:
            default_logger.info(
                f'You should see a demo page opened in your browser, '
                f'if not, you may open {url_html_path} manually'
            )
        if not args.unblock_query_flow:
            f.block()


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


if __name__ == '__main__':
    args = set_hw_multimodal_parser().parse_args()
    hello_world(args)
