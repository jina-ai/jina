import argparse

from .base import BaseRuntime
from .zed import ZEDRuntime


def Runtime(args: 'argparse.Namespace') -> 'BaseRuntime':
    return ZEDRuntime(args)
