from docarray import DocumentArray
from jina import Executor, requests
from jina.parsers import set_pod_parser


class ProcessExecutor(Executor):
    @requests(on='/')
    def process(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            doc.text = doc.text + 'world'
            doc.tags['processed'] = True


def _validate_dummy_custom_gateway_response(port, expected):
    import requests

    resp = requests.get(f'http://127.0.0.1:{port}/').json()
    assert resp == expected


def _validate_custom_gateway_process(port, text, expected):
    import requests

    resp = requests.get(f'http://127.0.0.1:{port}/stream?text={text}').json()
    assert resp == expected

# set_pod_parser returns a parser for worker runtime, which expects list of ports (because external executors
# can provide multiple ports and hosts). However this parser is not compatible with ContainerPod, Pod and worker runtime.
# Should we add a seperate parser for Pod?
def _generate_args(cli_split: list=[]):
    args = set_pod_parser().parse_args(cli_split)
    args.host = args.host[0]
    args.port = args.port[0]
    args.port_monitoring = args.port_monitoring[0]
    
    return args