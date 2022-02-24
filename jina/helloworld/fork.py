import os
import shutil
from typing import TYPE_CHECKING

from jina.logging.predefined import default_logger


if TYPE_CHECKING:
    from argparse import Namespace


def fork_hello(args: 'Namespace') -> None:
    """Fork the hello world demos into a new directory

    :param args: the arg from cli

    """
    from_path = os.path.join(os.path.dirname(__file__), args.project)
    shutil.copytree(from_path, args.destination)
    full_path = os.path.abspath(args.destination)
    default_logger.success(f'{args.project} project is forked to {full_path}')
    default_logger.info(
        f'''
    To run the project:
    ~$ cd {full_path}
    ~$ python app.py
    '''
    )
