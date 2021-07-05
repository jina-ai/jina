"""Argparser module for hub push"""
from ..helper import add_arg_group


def mixin_hub_pull_parser(parser):
    """Add the arguments for hub pull to the parser
    :param parser: the parser configure
    """

    def hub_uri(uri: str) -> str:
        from ...hubble.helper import parse_hub_uri

        parse_hub_uri(uri)
        return uri

    gp = add_arg_group(parser, title='Pull')
    gp.add_argument(
        'uri',
        type=hub_uri,
        help='The URI of the executor to pull (e.g., jinahub[+docker]://UUID8)',
    )
    gp.add_argument(
        '--install-requirements',
        action='store_true',
        default=False,
        help='If set, install `requirements.txt` in the Hub Executor bundle to the local system',
    )
