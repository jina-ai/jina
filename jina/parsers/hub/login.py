import os

from ..base import set_base_parser


def set_hub_login_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    parser.add_argument('--username', type=str, help='the Docker registry username',
                        default=os.environ.get('JINAHUB_USERNAME', ''))
    # _gp = parser.add_mutually_exclusive_group()
    # _gp.add_argument('--password-stdin', type=argparse.FileType('r'),
    #                  default=(sys.stdin if sys.stdin.isatty() else None),
    #                  help='take the password from stdin')
    parser.add_argument('--password', type=str, help='the plaintext password',
                        default=os.environ.get('JINAHUB_PASSWORD', ''))
    parser.add_argument('--registry', type=str, default='https://index.docker.io/v1/',
                        help='the URL to the Docker registry, e.g. https://index.docker.io/v1/')
    parser.add_argument('--repository', type=str, default='jinahub',
                        help='the Docker repository name, change this when pushing image to a personal repository')
    return parser
