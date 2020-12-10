import os

from jina.proto import jina_pb2
from jina.types.ndarray.generic import NdArray

from ..pods.components import MyEncoder
from ..pods.evaluate import MyEvaluator


def index_document_generator(num_doc, target):
    for j in range(num_doc):
        label_int = target["index-labels"]["data"][j][0]
        d = jina_pb2.DocumentProto()
        NdArray(d.blob).value = target["index"]["data"][j]
        d.tags["label_id"] = str(label_int)
        yield d


def evaluation_document_generator(num_doc, target):
    for j in range(num_doc):
        label_int = target["query-labels"]["data"][j][0]
        next_doc = jina_pb2.DocumentProto()
        NdArray(next_doc.blob).value = target["query"]["data"][j]

        groundtruth_doc = jina_pb2.DocumentProto()
        m1 = groundtruth_doc.matches.add()
        m1.tags["label_id"] = str(label_int)

        yield next_doc, groundtruth_doc