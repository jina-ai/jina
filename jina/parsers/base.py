"""Module containing the base parser for arguments of Jina."""
import argparse

from .helper import _chf


def set_base_parser():
    """Set the base parser

    :return: the parser
    """
    from .. import __version__
    from ..helper import colored, get_full_version, format_full_version_info

    # create the top-level parser
    urls = {
        'Jina 101': ('🐣', 'https://101.jina.ai'),
        'Docs': ('📚', 'https://docs.jina.ai'),
        'Examples': ('🚀‍', 'https://learn.jina.ai'),
        'Code': ('🧑‍💻', 'https://opensource.jina.ai'),
        'Hiring!': ('🙌', 'https://career.jina.ai'),
    }
    url_str = '\n'.join(
        f'- {v[0]:<10} {k:10.10}\t{colored(v[1], "cyan", attrs=["underline"])}'
        for k, v in urls.items()
    )

    parser = argparse.ArgumentParser(
        epilog=f'''
Jina (v{colored(__version__, "green")}) is the cloud-native neural search solution powered by AI & deep learning.
It is a universal solution to large-scale index and query of unstructured & multimedia data.

{url_str}

''',
        formatter_class=_chf,
        description='Command Line Interface of `%(prog)s`',
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
