import uuid
from argparse import Namespace

from jina.peapods import Pea
from .base import BaseStore


class PeaStore(BaseStore):
    """ Creates Pea/Pod on remote  """

    peapod_cls = Pea

    def add(self, args: Namespace, **kwargs):
        try:
            _id = uuid.UUID(args.identity)
            p = self.peapod_cls(args).start()
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self[_id] = {
                'object': p,
                'arguments': vars(args)
            }
            return _id
