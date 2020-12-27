import argparse

from .asyncio.rest import RESTRuntime
from .base import BaseRuntime
from .zed import ZEDRuntime


def Runtime(args: 'argparse.Namespace') -> 'BaseRuntime':
    return RESTRuntime(args)
