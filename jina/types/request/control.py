from typing import Dict

from . import Request

from .mixin import CommandMixin


class ControlRequest(Request, CommandMixin):
    """Control request class."""

    @property
    def args(self):
        """struct args


        .. #noqa: DAR201"""
        return self.proto._args

    @args.setter
    def args(self, value: Dict):
        self.args.update(value)
