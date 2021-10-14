"""Module for hello world argparser"""
import argparse

from .base import set_base_parser
from .helper import add_arg_group, _SHOW_ALL_ARGS, _chf
from ..helper import random_identity


def mixin_hw_base_parser(parser):
    """Add the arguments for hello world to the parser

    :param parser: the parser configure
    """
    gp = add_arg_group(parser, title='General')
    gp.add_argument(
        '--workdir',
        type=str,
        default=random_identity(),
        help='The workdir for hello-world demo'
        'all data, indices, shards and outputs will be saved there',
    )
    gp.add_argument(
        '--download-proxy', type=str, help='The proxy when downloading sample data'
    )


def set_hello_parser(parser=None):
    """
    Set the hello parser

    :param parser: the parser configure
    """

    if not parser:
        parser = set_base_parser()

    spp = parser.add_subparsers(
        dest='hello',
        description='use `%(prog)-8s [sub-command] --help` '
        'to get detailed information about each sub-command',
        required=True,
    )

    set_hw_parser(
        spp.add_parser(
            'fashion',
            help='Start a simple end2end fashion images index & search demo. '
            'This demo requires no extra dependencies.',
            description='Run a fashion search demo',
            formatter_class=_chf,
        )
    )

    set_hw_chatbot_parser(
        spp.add_parser(
            'chatbot',
            help='''
Start a simple Covid-19 chatbot.

Remarks:

- Pytorch, transformers & FastAPI are required to run this demo. To install all dependencies, use

    pip install "jina[demo]"

- The indexing could take 1~2 minute on a CPU machine.
''',
            description='Run a chatbot QA demo',
            formatter_class=_chf,
        )
    )

    set_hw_multimodal_parser(
        spp.add_parser(
            'multimodal',
            help='''
Start a simple multimodal document search.

Remarks:

- Pytorch, torchvision, transformers & FastAPI are required to run this demo. To install all dependencies, use

    pip install "jina[demo]"

- The indexing could take 2~3 minute on a CPU machine.
- Downloading the dataset could take ~1 minute depending on your network.
''',
            description='Run a multimodal search demo',
            formatter_class=_chf,
        )
    )

    set_hw_fork_parser(
        spp.add_parser(
            'fork',
            help='Fork a hello world project to a local directory, and start to build your own project on it.',
            description='Fork a hello world project to a local directory.',
            formatter_class=_chf,
        )
    )


def set_hw_parser(parser=None):
    """Set the hello world parser

    :param parser: the parser configure
    :return: the new parser
    """
    if not parser:
        parser = set_base_parser()

    mixin_hw_base_parser(parser)
    gp = add_arg_group(parser, title='Index')
    gp.add_argument(
        '--index-data-url',
        type=str,
        default='http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/train-images-idx3-ubyte.gz',
        help='The url of index data (should be in idx3-ubyte.gz format)',
    )
    gp.add_argument(
        '--index-labels-url',
        type=str,
        default='http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/train-labels-idx1-ubyte.gz',
        help='The url of index labels data (should be in idx3-ubyte.gz format)',
    )

    gp = add_arg_group(parser, title='Search')
    gp.add_argument(
        '--query-data-url',
        type=str,
        default='http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/t10k-images-idx3-ubyte.gz',
        help='The url of query data (should be in idx3-ubyte.gz format)',
    )
    gp.add_argument(
        '--query-labels-url',
        type=str,
        default='http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/t10k-labels-idx1-ubyte.gz',
        help='The url of query labels data (should be in idx3-ubyte.gz format)',
    )

    gp.add_argument(
        '--num-query', type=int, default=128, help='The number of queries to visualize'
    )
    gp.add_argument(
        '--top-k', type=int, default=50, help='Top-k results to retrieve and visualize'
    )
    return parser


def set_hw_chatbot_parser(parser=None):
    """Set the parser for the hello world chatbot

    :param parser: the parser configure
    :return: the new parser
    """
    if not parser:
        parser = set_base_parser()

    mixin_hw_base_parser(parser)
    parser.add_argument(
        '--index-data-url',
        type=str,
        default='https://static.jina.ai/chatbot/dataset.csv',
        help='The url of index csv data',
    )
    parser.add_argument(
        '--port-expose',
        type=int,
        default=8080,
        help='The port of the host exposed to the public',
    )
    parser.add_argument(
        '--replicas',
        type=int,
        default=2,
        help='The number of replicas when index and query',
    )
    parser.add_argument(
        '--unblock-query-flow',
        action='store_true',
        default=False,
        help='Do not block the query flow' if _SHOW_ALL_ARGS else argparse.SUPPRESS,
    )
    return parser


def set_hw_fork_parser(parser=None):
    """Set the parser for forking hello world demo

    :param parser: the parser configure
    :return: the new parser
    """
    if not parser:
        parser = set_base_parser()

    parser.add_argument(
        'project',
        type=str,
        choices=['fashion', 'chatbot', 'multimodal'],
        help='The hello world project to fork',
    )

    parser.add_argument(
        'destination',
        type=str,
        help='The dest directory of the forked project. Note, it can not be an existing path.',
    )

    return parser


def set_hw_multimodal_parser(parser=None):
    """Set the parser for the hello world multimodal

    :param parser: the parser configure
    :return: the new parser
    """

    if not parser:
        parser = set_base_parser()

    mixin_hw_base_parser(parser)
    parser.add_argument(
        '--index-data-url',
        type=str,
        default='https://static.jina.ai/multimodal/people-img.zip',
        help='The url of index csv data',
    )
    parser.add_argument(
        '--port-expose',
        type=int,
        default=8080,
        help='The port of the host exposed to the public',
    )
    parser.add_argument(
        '--unblock-query-flow',
        action='store_true',
        default=False,
        help='Do not block the query flow' if _SHOW_ALL_ARGS else argparse.SUPPRESS,
    )
    return parser
