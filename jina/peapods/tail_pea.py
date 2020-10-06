__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import argparse
from typing import Dict, Union
from .pea import BasePea
from ..logging import JinaLogger


class TailPea(BasePea):

    def __init__(self, args: Union['argparse.Namespace', Dict]):
        super().__init__(args)
        self.name = self.__class__.__name__
        if isinstance(self.args, argparse.Namespace):
            if self.args.name:
                self.name = self.args.name
                self.name = f'{self.name}-tail'
            self.logger = JinaLogger(self.name, **vars(self.args))
        else:
            self.logger = JinaLogger(self.name)

    def __str__(self):
        return self.name
