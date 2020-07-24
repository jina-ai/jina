__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import argparse
from typing import Dict, Union
from ..enums import OnErrorSkip
from ..executors import BaseExecutor
from ..proto import jina_pb2
from .pea import BasePea


class SplitterPea(BasePea):

    def __init__(self, args: Union['argparse.Namespace', Dict]):
        super().__init__(args)

    def load_executor(self):
        """Load the executor to this SplitterPea, specified by ``uses`` CLI argument.
        Force it to be attached to `_route_split`
        """
        # TODO: Change executor to _route_split which in the resources will be attached to SplitterDriver
        super().load_executor()
        self.splitter_executor = BaseExecutor.load_config('_splitroute')
        self.splitter_executor.attach(pea=self)

    def handle(self) -> 'BasePea':
        # TODO: Once output message is assigned at driver level, this handle can disappear
        """Call the executor to handle this message if its envelope's status is not ERROR, else skip handling of message.
        """
        super().handle()
        if self.message_in.envelope.status.code != jina_pb2.Status.ERROR or self.args.skip_on_error < OnErrorSkip.HANDLE:
            self.splitter_executor(self.request_type)
        return self
