import os
import shutil
import sys
import unittest
from os.path import dirname

import numpy as np

from jina.drivers.helper import array2pb
from jina.proto import jina_pb2


class JinaTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp_files = []
        os.environ['TEST_WORKDIR'] = os.getcwd()

    def tearDown(self) -> None:
        for k in self.tmp_files:
            if os.path.exists(k):
                if os.path.isfile(k):
                    os.remove(k)
                elif os.path.isdir(k):
                    shutil.rmtree(k, ignore_errors=False, onerror=None)

    def add_tmpfile(self, *path):
        self.tmp_files.extend(path)


file_dir = os.path.dirname(__file__)
sys.path.append(dirname(file_dir))


def random_docs(num_docs, chunks_per_doc=5, embed_dim=10):
    c_id = 0
    for j in range(num_docs):
        d = jina_pb2.Document()
        d.id = j
        d.text = b'hello world'
        d.embedding.CopyFrom(array2pb(np.random.random([embed_dim])))
        for k in range(chunks_per_doc):
            c = d.chunks.add()
            c.text = 'i\'m chunk %d from doc %d' % (c_id, j)
            c.embedding.CopyFrom(array2pb(np.random.random([embed_dim])))
            c.id = c_id
            c.parent_id = j
            c_id += 1
        yield d


def rm_files(file_paths):
    for file_path in file_paths:
        if os.path.exists(file_path):
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path, ignore_errors=False, onerror=None)