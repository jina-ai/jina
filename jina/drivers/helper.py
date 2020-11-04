__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import mimetypes
import urllib.parse
import urllib.request
from typing import Dict, Any, Iterable, Tuple

import numpy as np

from ..proto import jina_pb2
from ..proto.ndarray.generic import GenericNdArray


def extract_docs(docs: Iterable['jina_pb2.Document'], embedding: bool) -> Tuple:
    """Iterate over a list of protobuf documents and extract chunk-level information from them

    :param docs: an iterable of protobuf documents
    :param embedding: an indicator of extracting embedding or not.
                    If ``True`` then all doc-level embedding are extracted.
                    If ``False`` then ``text``, ``buffer``, ``blob`` info of each doc are extracted
    :return: A tuple of 3 pieces:

            - a numpy ndarray of extracted info
            - the corresponding doc references
            - the doc_id list where the doc has no contents, useful for debugging
    """
    contents = []
    docs_pts = []
    bad_doc_ids = []

    if embedding:
        _extract_fn = lambda doc: GenericNdArray(doc.embedding).value
    else:
        _extract_fn = lambda doc: doc.text or doc.buffer or GenericNdArray(doc.blob).value

    for doc in docs:
        content = _extract_fn(doc)

        if content is not None:
            contents.append(content)
            docs_pts.append(doc)
        else:
            bad_doc_ids.append((doc.id, doc.parent_id))

    contents = np.stack(contents) if contents else None
    return contents, docs_pts, bad_doc_ids


def pb_obj2dict(obj, keys: Iterable[str]) -> Dict[str, Any]:
    """Convert a protobuf object to a Dict by selected keys

    :param obj: a protobuf object
    :param keys: an iterable of keys for extraction
    """
    ret = {k: getattr(obj, k) for k in keys if hasattr(obj, k)}
    if 'blob' in ret:
        ret['blob'] = GenericNdArray(obj.blob).value
    return ret


def guess_mime(uri):
    # guess when uri points to a local file
    m_type = mimetypes.guess_type(uri)[0]
    # guess when uri points to a remote file
    if not m_type and urllib.parse.urlparse(uri).scheme in {'http', 'https', 'data'}:
        page = urllib.request.Request(uri, headers={'User-Agent': 'Mozilla/5.0'})
        tmp = urllib.request.urlopen(page)
        m_type = tmp.info().get_content_type()
    return m_type


class DocGroundtruthPair:
    """
    Helper class to expose common interface to the traversal logic of the BaseExecutable Driver.
    It is important to note that it checks the matching structure of `docs` and `groundtruths`. It is important while
    traversing to ensure that then the driver can be applied at a comparable level of granularity and adjacency.
    This does not imply that you can't compare at the end a document with 10 matches with a groundtruth with 20 matches
    """

    def __init__(self, doc: 'jina_pb2.Document', groundtruth: 'jina_pb2.Document'):
        self.doc = doc
        self.groundtruth = groundtruth

    @property
    def matches(self):
        assert self.groundtruth and len(self.doc.matches) == len(self.groundtruth.matches)
        for doc, groundtruth in zip(self.doc.matches, self.groundtruth.matches):
            yield DocGroundtruthPair(doc, groundtruth)

    @property
    def chunks(self):
        assert self.groundtruth and len(self.doc.chunks) == len(self.groundtruth.chunks)
        for doc, groundtruth in zip(self.doc.chunks, self.groundtruth.chunks):
            yield DocGroundtruthPair(doc, groundtruth)
