from .helper import add_arg_group
from ..enums import RequestType


def mixin_client_cli_parser(parser):
    gp = add_arg_group(parser, title='Client')

    # TODO (Joan): Remove `--batch-size` alias whenever the examples and documentations are updated
    gp.add_argument('--request-size', '--batch-size', type=int, default=100,
                    help='the number of documents in each request')
    gp.add_argument('--mode', choices=list(RequestType), type=RequestType.from_string,
                    # required=True,
                    help='the mode of the client and the server')
    gp.add_argument('--top-k', type=int,
                    help='top_k results returned in the search mode')
    gp.add_argument('--mime-type', type=str,
                    help='MIME type of the input, useful when input-type is set to BUFFER')
    gp.add_argument('--continue-on-error', action='store_true', default=False,
                    help='if to continue on all requests when callback function throws an error')
    gp.add_argument('--return-results', action='store_true', default=False,
                    help='if to return all results as a list')
