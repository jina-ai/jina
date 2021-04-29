__copyright__ = "Copyright (c) 2021 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"


class TrainerMixin(object):
    """
    Interface of trainer for Rankers.
    """

    def losses(self):
        return self._losses

