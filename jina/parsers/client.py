from .base import set_base_parser
from .helper import add_arg_group


def set_client_cli_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    from ..enums import RequestType, CallbackOnType

    _set_grpc_parser(parser)

    gp1 = add_arg_group(parser, 'client-specific arguments')

    gp1.add_argument('--batch-size', type=int, default=100,
                     help='the number of documents in each request')
    gp1.add_argument('--mode', choices=list(RequestType), type=RequestType.from_string,
                     # required=True,
                     help='the mode of the client and the server')
    gp1.add_argument('--top-k', type=int,
                     help='top_k results returned in the search mode')
    gp1.add_argument('--mime-type', type=str,
                     help='MIME type of the input, useful when input-type is set to BUFFER')
    gp1.add_argument('--callback-on', choices=list(CallbackOnType), type=CallbackOnType.from_string,
                     default=CallbackOnType.REQUEST,
                     help='which field the output function should work with')
    gp1.add_argument('--timeout-ready', type=int, default=10000,
                     help='timeout (ms) of a pea is ready for request, -1 for waiting forever')
    gp1.add_argument('--skip-dry-run', action='store_true', default=False,
                     help='skip dry run (connectivity test) before sending every request')
    gp1.add_argument('--continue-on-error', action='store_true', default=False,
                     help='if to continue on all requests when callback function throws an error')
    return parser
