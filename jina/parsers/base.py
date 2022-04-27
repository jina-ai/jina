"""Module containing the base parser for arguments of Jina."""
import argparse

from jina.parsers.helper import _chf


def set_base_parser():
    """Set the base parser

    :return: the parser
    """
    from jina import __version__
    from jina.helper import colored, format_full_version_info, get_full_version

    # create the top-level parser
    urls = {
        'Code': ('💻', 'https://github.com/jina-ai/jina'),
        'Docs': ('📖', 'https://docs.jina.ai'),
        'Help': ('💬', 'https://slack.jina.ai'),
        'Hiring!': ('🙌', 'https://career.jina.ai'),
    }
    url_str = '\n'.join(
        f'- {v[0]:<10} {k:10.10}\t{colored(v[1], "cyan", attrs=["underline"])}'
        for k, v in urls.items()
    )

    parser = argparse.ArgumentParser(
        epilog=f'''
Jina (v{colored(__version__, "green")}) is the cloud-native neural search framework powered by deep learning.

{url_str}

''',
        formatter_class=_chf,
    )
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version=__version__,
        help='Show Jina version',
    )

    parser.add_argument(
        '-vf',
        '--version-full',
        action='version',
        version=format_full_version_info(*get_full_version()),
        help='Show Jina and all dependencies\' versions',
    )
    return parser
