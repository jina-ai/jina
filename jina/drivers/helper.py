__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import mimetypes
import os
import urllib.parse
import urllib.request
from typing import Dict, Any, Iterable, Tuple

import numpy as np

from ..proto import jina_pb2


def pb2array(blob: 'jina_pb2.NdArray') -> 'np.ndarray':
    """Convert a blob protobuf to a numpy ndarray.

    Note if the argument ``quantize`` is specified in :func:`array2pb` then the returned result may be lossy.
    Nonetheless, it will always in original ``dtype``, i.e. ``float32`` or ``float64``

    :param blob: a blob described in protobuf
    """
    x = np.frombuffer(blob.buffer, dtype=blob.dtype)

    if blob.quantization == jina_pb2.NdArray.FP16:
        x = x.astype(blob.original_dtype)
    elif blob.quantization == jina_pb2.NdArray.UINT8:
        x = x.astype(blob.original_dtype) * blob.scale + blob.min_val

    return x.reshape(blob.shape)


def array2pb(x: 'np.ndarray', quantize: str = None) -> 'jina_pb2.NdArray':
    """Convert a numpy ndarray to blob protobuf.

    :param x: the target ndarray
    :param quantize: the quantization method used when converting to protobuf.
            Availables are ``fp16``, ``uint8``, default is None.

    Remarks on quantization:
        The quantization only works when ``x`` is in ``float32`` or ``float64``. The motivation is to
        save the network bandwidth by using less bits to store the numpy array in the protobuf.

            - ``fp16`` quantization is lossless, can be used widely. Each float is represented by 16 bits.
            - ``uint8`` quantization is lossy. Each float is represented by 8 bits. The algorithm behind is standard scaling.

        There is no need to specify the quantization type in :func:`pb2array`,
        as the quantize type is stored and the blob is self-contained to recover the original numpy array
    """
    blob = jina_pb2.NdArray()

    quantize = os.environ.get('JINA_ARRAY_QUANT', quantize)

    if quantize == 'fp16' and (x.dtype == np.float32 or x.dtype == np.float64):
        blob.quantization = jina_pb2.NdArray.FP16
        blob.original_dtype = x.dtype.name
        x = x.astype(np.float16)
    elif quantize == 'uint8' and (x.dtype == np.float32 or x.dtype == np.float64 or x.dtype == np.float16):
        blob.quantization = jina_pb2.NdArray.UINT8
        blob.max_val, blob.min_val = x.max(), x.min()
        blob.original_dtype = x.dtype.name
        blob.scale = (blob.max_val - blob.min_val) / 256
        x = ((x - blob.min_val) / blob.scale).astype(np.uint8)
    else:
        blob.quantization = jina_pb2.NdArray.NONE

    blob.buffer = x.tobytes()
    blob.shape.extend(list(x.shape))
    blob.dtype = x.dtype.str
    return blob


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
        _extract_fn = lambda doc: (doc.embedding.buffer or None) and pb2array(doc.embedding)
    else:
        _extract_fn = lambda doc: doc.text or doc.buffer or (doc.blob and pb2array(doc.blob))

    for doc in docs:
        content = _extract_fn(doc)

        if content is not None:
            contents.append(content)
            docs_pts.append(doc)
        else:
            bad_doc_ids.append((doc.id, doc.parent_id))

    contents = np.stack(contents) if contents else None
    return contents, docs_pts, bad_doc_ids


def routes2str(msg: 'jina_pb2.Message', flag_current: bool = False) -> str:
    """Get the string representation of the routes in a message.

    :param msg: a protobuf message
    :param flag_current: flag the current :class:`BasePod` as ``⚐``
    """
    route_str = [r.pod for r in msg.envelope.routes]
    if flag_current:
        route_str.append('⚐')
    from ..helper import colored
    return colored('▸', 'green').join(route_str)


def add_route(evlp: 'jina_pb2.Envelope', name: str, identity: str) -> None:
    """Add a route to the envelope

    :param evlp: the envelope to modify
    :param name: the name of the pod service
    :param identity: the identity of the pod service
    """
    r = evlp.routes.add()
    r.pod = name
    r.start_time.GetCurrentTime()
    r.pod_id = identity


def pb_obj2dict(obj, keys: Iterable[str]) -> Dict[str, Any]:
    """Convert a protobuf object to a Dict by selected keys

    :param obj: a protobuf object
    :param keys: an iterable of keys for extraction
    """
    ret = {k: getattr(obj, k) for k in keys if hasattr(obj, k)}
    if 'blob' in ret:
        ret['blob'] = pb2array(obj.blob)
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
        # TODO: Should we expect this assert to be done
        #  (RankingEvaluation may work with a different lenght of groundtruth matches as the one returned)
        assert len(self.doc.matches) == len(self.groundtruth.matches)
        return [DocGroundtruthPair(doc, groundtruth) for doc, groundtruth in
                zip(self.doc.matches, self.groundtruth.matches)]

    @property
    def chunks(self):
        assert len(self.doc.chunks) == len(self.groundtruth.chunks)
        return [DocGroundtruthPair(doc, groundtruth) for doc, groundtruth in
                zip(self.doc.chunks, self.groundtruth.chunks)]
