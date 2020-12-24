import argparse

from .base import BaseRuntime


def Runtime(args: 'argparse.Namespace') -> 'BaseRuntime':
    raise NotImplementedError
