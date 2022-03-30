from jina.parsers.base import set_base_parser
from jina.parsers.helper import _ColoredHelpFormatter as _chf


def set_start_parser(sp=None):
    """Add the arguments for jina now start to the parser
    :param sp: an optional existing parser to build upon
    """

    parser = sp.add_parser(
        'start',
        help='Start jina now and create or reuse a cluster.',
        description='Start jina now and create or reuse a cluster.',
        formatter_class=_chf,
    )

    parser.add_argument(
        '--data',
        help='Select one of the available datasets or provide local filepath, '
        'docarray url, or docarray secret to use your own dataset',
        type=str,
    )

    parser.add_argument(
        '--quality',
        help='Choose the quality of the model that you would like to finetune',
        type=str,
    )

    parser.add_argument(
        '--cluster',
        help='Choose the quality of the model that you would like to finetune',
        type=str,
    )


def set_stop_parser(sp):
    """Add the arguments for jina now stop to the parser
    :param sp: an optional existing parser to build upon
    """
    sp.add_parser(
        'stop',
        help='Stop jina now and remove local cluster.',
        description='Stop jina now and remove local cluster.',
        formatter_class=_chf,
    )


def set_now_parser(parser=None):
    """Set the parser for the API export

    :param parser: an optional existing parser to build upon
    :return: the parser
    """
    if not parser:
        parser = set_base_parser()

    spp = parser.add_subparsers(
        dest='now',
        description='use `%(prog)-8s [sub-command] --help` '
        'to get detailed information about each sub-command',
        required=True,
    )

    set_start_parser(spp)
    set_stop_parser(spp)
    return parser
