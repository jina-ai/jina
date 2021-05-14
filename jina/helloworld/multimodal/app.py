import os
import csv
import webbrowser
from pathlib import Path

from pkg_resources import resource_filename

from jina import Flow, Document, DocumentArray
from jina.importer import ImportExtensions
from jina.logging import default_logger
from jina.helloworld.multimodal.helper import download_data


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
        import transformers, torch

        assert [torch, transformers]  #: prevent pycharm auto remove the above line

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
    with open(f'{args.workdir}/people-img/meta.csv', newline='') as fp:
        lines = list(csv.reader(fp))

    document_array = DocumentArray()
    for line in lines[1:200]:
        _, img_name, caption = line
        document_array.append(Document(tags={'caption': caption, 'image': img_name}))

    with Flow.load_config('flow-index.yml') as f:
        f.post(on='/index', inputs=document_array, request_size=12)

    # search it!
    f = Flow.load_config('flow-search.yml')
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
