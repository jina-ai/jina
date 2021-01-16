import uuid
from argparse import Namespace

from jina.peapods import Pea
from .base import BaseStore
from ..excepts import PeaStartException


class PeaStore(BaseStore):
    """ Creates Pea/Pod on remote  """

    peapod_cls = Pea

    def add(self, args: Namespace, **kwargs):
        try:
            _id = uuid.UUID(args.identity)
            p = self.peapod_cls(args).start()
        except Exception as e:
            self._logger.error('{e!r}')
            raise PeaStartException from e
        else:
            self._items[_id] = {'object': p}
            return _id
