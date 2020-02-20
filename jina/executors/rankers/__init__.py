from typing import Dict

import numpy as np

from .. import BaseExecutor


class BaseRanker(BaseExecutor):
    """The base class for a `Ranker`. A `Ranker` translates the chunk-wise score (distance) to the doc-wise score.

    In the query-time, :class:`BaseRanker` is an almost-always required component.
    Because in the end we want to retrieve top-k documents of given query-document not top-k chunks of
    given query-chunks. The purpose of :class:`BaseRanker` is to aggregate the already existed top-k chunks
    into documents.

    The key function here is :func:`score`.

    .. seealso::
        :mod:`jina.drivers.handlers.score`

    """

    required_keys = {}  #: a set of ``str``, key-values to extracted from the chunk-level protobuf message

    def score(self, match_idx: 'np.ndarray', query_chunk_meta: Dict, match_chunk_meta: Dict) -> 'np.ndarray':
        """Translate the chunk-level top-k results into doc-level top-k results. Some score functions may leverage the
        meta information of the query, hence the meta info of the query chunks and matched chunks are given
        as arguments.

        :param match_idx: a [N x 4] numpy ``ndarray``, column-wise:

                - ``match_idx[:,0]``: ``doc_id`` of the matched chunks, integer
                - ``match_idx[:,1]``: ``chunk_id`` of the matched chunks, integer
                - ``match_idx[:,2]``: ``chunk_id`` of the query chunks, integer
                - ``match_idx[:,3]``: distance/metric/score between the query and matched chunks, float
        :param query_chunk_meta: the meta information of the query chunks, where the key is query chunks' ``chunk_id``,
            the value is extracted by the ``required_keys``.
        :param match_chunk_meta: the meta information of the matched chunks, where the key is matched chunks' ``chunk_id``,
            the value is extracted by the ``required_keys``.
        :return: a [N x 2] numpy ``ndarray``, where the first column is the matched documents' ``doc_id`` (integer)
                the second column is the score/distance/metric between the matched doc and the query doc (float).
        """
        raise NotImplementedError
