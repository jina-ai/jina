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
        if isinstance(args, argparse.Namespace):
            if args.name:
                self.name = args.name
                self.name = f'{self.name}-head'
            self.logger = get_logger(self.name, **vars(args))
        else:
            self.logger = get_logger(self.name)
