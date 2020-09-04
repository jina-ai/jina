import numpy as np

from jina.drivers.helper import array2pb
from jina.flow import Flow
from jina.proto import jina_pb2

f = Flow().add(uses='yaml/test-adjacency.yml')


def random_docs(num_docs):
    vecs = np.random.random([num_docs, 2])
    for j in range(num_docs):
        d = jina_pb2.Document()
        d.id = j
        d.embedding.CopyFrom(array2pb(vecs[j]))
        yield d


with f:
    f.index(random_docs(100))

with f:
    f.search(random_docs(10), output_fn=print)
