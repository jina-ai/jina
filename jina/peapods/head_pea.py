__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import argparse
from typing import Dict, Union
from .pea import BasePea
from ..logging import get_logger


class HeadPea(BasePea):
    
    def __init__(self, args: Union['argparse.Namespace', Dict]):
        super().__init__(args)
        self.name = self.__class__.__name__

    def post_init(self):
        """Post initializer after the start of the request loop via :func:`run`, so that they can be kept in the same
        process/thread as the request loop.

        """
        if isinstance(self.args, argparse.Namespace):
            if self.args.name:
                self.name = self.args.name
                self.name = f'{self.name}-head'
            self.logger = get_logger(self.name, **vars(self.args))
        else:
            self.logger = get_logger(self.name)

    def __str__(self):
        return self.name