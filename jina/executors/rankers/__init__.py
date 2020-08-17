__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from .. import BaseExecutor


class BaseRanker(BaseExecutor):
    """The base class for a `Ranker`"""

    def score(self, *args, **kwargs):
        raise NotImplementedError
