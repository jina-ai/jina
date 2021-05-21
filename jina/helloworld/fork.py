import os
import shutil

from jina.logging import default_logger


def fork_hello(args):
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
