import os
import webbrowser
from pathlib import Path

from pkg_resources import resource_filename

from .. import download_data
from ... import Flow
from ...importer import ImportExtensions
from ...logging import default_logger


def hello_world(args):
    Path(args.workdir).mkdir(parents=True, exist_ok=True)

    with ImportExtensions(required=True, help_text='this demo requires Pytorch and Transformers to be installed, '
                                                   'if you haven\'t, please do `pip install jina[torch,transformers]`'):
        import transformers, torch
        assert [torch, transformers]  #: prevent pycharm auto remove the above line

    targets = {
        'covid-csv': {
            'url': args.index_data_url,
            'filename': os.path.join(args.workdir, 'dataset.csv')
        }
    }

    # download the data
    download_data(targets, args.download_proxy, task_name='download csv data')

    # this envs are referred in index and query flow YAMLs
    os.environ['HW_WORKDIR'] = args.workdir

    # now comes the real work
    # load index flow from a YAML file

    f = (Flow()
         .add(uses='TransformerTorchEncoder', parallel=args.parallel)
         .add(uses=f'{resource_filename("jina", "resources")}/helloworld.indexer.yml'))

    # index it!
    with f, open(targets['covid-csv']['filename']) as fp:
        f.index_csv(fp, field_resolver={'question': 'text',
                                        'url': 'uri'})

    # switch to REST gateway
    f.use_rest_gateway(args.port_expose)
    with f:
        try:
            webbrowser.open(args.demo_url, new=2)
        except:
            pass  # intentional pass, browser support isn't cross-platform
        finally:
            default_logger.success(f'You should see a chatbot page opened in your browser, '
                                   f'if not you may open {args.demo_url} manually')
        if not args.unblock_query_flow:
            f.block()
