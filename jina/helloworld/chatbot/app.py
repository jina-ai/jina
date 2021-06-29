import os
import urllib.request
import webbrowser
from pathlib import Path

from jina import Flow
from jina.importer import ImportExtensions
from jina.logging.predefined import default_logger
from jina.logging.profile import ProgressBar
from jina.parsers.helloworld import set_hw_chatbot_parser
from jina.types.document.generators import from_csv

if __name__ == '__main__':
    from my_executors import MyTransformer, MyIndexer
else:
    from .my_executors import MyTransformer, MyIndexer


def _get_flow(args):
    """Ensure the same flow is used in hello world example and system test."""
    return (
        Flow(cors=True)
        .add(uses=MyTransformer, parallel=args.parallel)
        .add(uses=MyIndexer, workspace=args.workdir)
    )


def hello_world(args):
    """
    Execute the chatbot example.

    :param args: arguments passed from CLI
    """
    Path(args.workdir).mkdir(parents=True, exist_ok=True)

    with ImportExtensions(
        required=True,
        help_text='this demo requires Pytorch and Transformers to be installed, '
        'if you haven\'t, please do `pip install jina[torch,transformers]`',
    ):
        import transformers, torch

        assert [torch, transformers]  #: prevent pycharm auto remove the above line

    targets = {
        'covid-csv': {
            'url': args.index_data_url,
            'filename': os.path.join(args.workdir, 'dataset.csv'),
        }
    }

    # download the data
    download_data(targets, args.download_proxy, task_name='download csv data')

    # now comes the real work
    # load index flow from a YAML file

    f = _get_flow(args)

    # index it!
    with f, open(targets['covid-csv']['filename']) as fp:
        f.index(from_csv(fp, field_resolver={'question': 'text'}), show_progress=True)

        # switch to REST gateway at runtime
        f.protocol = 'http'
        f.port_expose = args.port_expose

        url_html_path = 'file://' + os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)), 'static/index.html'
            )
        )
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
    with ProgressBar(task_name=task_name) as t:
        for k, v in targets.items():
            if not os.path.exists(v['filename']):
                urllib.request.urlretrieve(
                    v['url'], v['filename'], reporthook=lambda *x: t.update_tick(0.01)
                )


if __name__ == '__main__':
    args = set_hw_chatbot_parser().parse_args()
    hello_world(args)
