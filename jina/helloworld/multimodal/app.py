import os
import webbrowser
from pathlib import Path

from jina import Flow, Document
from jina.importer import ImportExtensions
from jina.logging import default_logger
from jina.parsers.helloworld import set_hw_multimodal_parser
from .helper import download_data


def search(query_document, on_done_callback, on_fail_callback, top_k):
    with Flow.load_config('flow-search.yml') as f:
        f.search(
            inputs=query_document,
            on_done=on_done_callback,
            on_fail=on_fail_callback,
            parameters={'top_k': top_k},
        )


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
        import transformers, torch, torchvision

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
    download_data(targets, args.download_proxy, task_name='download zip data')
    import zipfile

    with zipfile.ZipFile(targets['people-img']['filename'], 'r') as fp:
        fp.extractall(args.workdir)

    # this envs are referred in index and query flow YAMLs
    os.environ['HW_WORKDIR'] = args.workdir
    # now comes the real work
    # load index flow from a YAML file

    # index it!
    f = Flow.load_config('flow-index.yml')

    with f, open(f'{args.workdir}/people-img/meta.csv', newline='') as fp:
        f.index(inputs=Document.from_csv(fp, size=10), request_size=10)

    # search it!
    f = Flow.load_config('flow-search.yml')
    # switch to REST gateway
    f.use_rest_gateway(args.port_expose)

    url_html_path = 'file://' + os.path.abspath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static/index.html')
    )
    with f:
        try:
            webbrowser.open(url_html_path, new=2)
        except:
            pass  # intentional pass, browser support isn't cross-platform
        finally:
            default_logger.success(
                f'You should see a demo page opened in your browser, '
                f'if not, you may open {url_html_path} manually'
            )
        if not args.unblock_query_flow:
            f.block()


if __name__ == '__main__':
    args = set_hw_multimodal_parser().parse_args()
    hello_world(args)
