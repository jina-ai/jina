from jina.parsers.base import set_base_parser
from jina.parsers.peapods.runtimes.remote import mixin_remote_parser


def get_main_parser():
    parser = set_base_parser()

    mixin_remote_parser(parser)

    parser.set_defaults(port_expose=8000)

    return parser
