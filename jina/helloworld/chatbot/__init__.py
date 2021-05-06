import os
import webbrowser
from pathlib import Path

from jina import Flow, Document
from jina.importer import ImportExtensions
from jina.logging import default_logger
from .helper import download_data


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
    from .executors import MyTransformer, MyIndexer

    f = (
        Flow()
            .add(uses=MyTransformer, parallel=args.parallel)
            .add(uses=MyIndexer)
    )

    # index it!
    with f, open(targets['covid-csv']['filename']) as fp:
        f.index(Document.from_csv(fp, field_resolver={'question': 'text', 'url': 'uri'}))

    # switch to REST gateway
    f.use_rest_gateway(args.port_expose)
    with f:
        try:
            webbrowser.open(args.demo_url, new=2)
        except:
            pass  # intentional pass, browser support isn't cross-platform
        finally:
            default_logger.success(
                f'You should see a demo page opened in your browser, '
                f'if not, you may open {args.demo_url} manually'
            )
        if not args.unblock_query_flow:
            f.block()
