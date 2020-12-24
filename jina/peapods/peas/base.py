import argparse

from ...enums import PeaRoleType
from ...logging import JinaLogger


class BasePea:

    def serve_forever(self):
        raise NotImplementedError

    def setup(self):
        pass

    def teardown(self):
        pass

    def cancel(self):
        raise NotImplementedError
