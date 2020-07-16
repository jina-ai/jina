__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from collections import defaultdict
from typing import Dict, List, Iterable

from . import BaseRecursiveDriver
from ..excepts import NoExplicitMessage
from ..proto import jina_pb2


class BaseReduceDriver(BaseRecursiveDriver):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._prev_requests = None
        self._prev_messages = None
        self._pending_msgs = defaultdict(list)  # type: Dict[str, List]

    @property
    def prev_reqs(self) -> List['jina_pb2.Request']:
        """Get all previous requests that has the same ``request_id``, shortcut to ``self.pea.prev_requests``

        This returns ``None`` when ``num_part=1``.
        """
        return self._prev_requests

    @property
    def prev_msgs(self) -> List['jina_pb2.Message']:
        """Get all previous messages that has the same ``request_id``, shortcut to ``self.pea.prev_messages``

        This returns ``None`` when ``num_part=1``.
        """
        return self._prev_messages

    def __call__(self, *args, **kwargs):
        if self.envelope.num_part[-1] > 1:
            req_id = self.envelope.request_id
            self._pending_msgs[req_id].append(self.msg)
            num_req = len(self._pending_msgs[req_id])

            self.logger.info(f'collected {num_req}/{self.envelope.num_part[-1]} parts of {type(self.req).__name__}')

            if num_req == self.envelope.num_part[-1]:
                self._prev_messages = self._pending_msgs.pop(req_id)
                self._prev_requests = [getattr(v.request, v.request.WhichOneof('body')) for v in
                                       self._prev_messages]
            else:
                raise NoExplicitMessage

            self.reduce(*args, **kwargs)
            self.envelope.num_part.pop(-1)

    def reduce(self, *args, **kwargs):
        super().__call__(*args, **kwargs)


class MergeDriver(BaseReduceDriver):
    """Merge the routes information from multiple envelopes into one """

    def reduce(self, *args, **kwargs):
        # take unique routes by service identity
        routes = {(r.pod + r.pod_id): r for m in self.prev_msgs for r in m.envelope.routes}
        self.msg.envelope.ClearField('routes')
        self.msg.envelope.routes.extend(
            sorted(routes.values(), key=lambda x: (x.start_time.seconds, x.start_time.nanos)))


class MergeTopKDriver(MergeDriver):
    """Merge the topk results from multiple messages into one and sorted

    Useful in indexer sharding (i.e. ``--replicas > 1``)

    Complexity depends on the level:
         - ``level=chunk``: D x C x K x R
         - ``level=doc``: D x K x R

    where:
        - D is the number of queries
        - C is the number of chunks per query
        - K is the top-k
        - R is the number of shards (i.e. ``--replicas``)
    """

    def reduce(self, *args, **kwargs):
        BaseRecursiveDriver.__call__(self, *args, **kwargs)
        super().reduce(*args, **kwargs)

    def apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs):
        for _d_id, _doc in enumerate(docs):
            _flat_topk = [k for r in self.prev_reqs for k in r.docs[_d_id].matches]
            _doc.ClearField('matches')
            _doc.matches.extend(sorted(_flat_topk, key=lambda x: x.score.value))
