import os
from typing import Any

import pytest
import numpy as np

from jina.executors.encoders import BaseEncoder
from jina.drivers.encode import EncodeDriver
from jina.flow import Flow
from jina import Document, NdArray


class MockEncoder(BaseEncoder):
    def __init__(self,
                 driver_batch_size: int,
                 num_docs_in_same_request: int,
                 total_num_docs: int,
                 *args, **kwargs):
        """
        This MockEncoder is used to test in very detail that the `batch_size` parameter of the driver works perfectly in detail.

        It takes into account the 'batch_size' provided to the driver, the number of 'documents' (counting also chunks and chunks of chunks)
        expected to happen in a single request, and the total number of documents expected to process.

        In general, it is expected that `data` will arrive in batches of `driver_batch_size` except at the end of a request (where
        some document "leftovers" are left to batch or at the end of the total process

        :param driver_batch_size: the batch_size at which to accumulate for encode driver
        :param num_docs_in_same_request: batch size of the request
        :param total_num_docs: the total_num_docs that will be sent in the test, important to know how large
        the last batches should be
        """
        super().__init__(*args, **kwargs)
        self.driver_batch_size = driver_batch_size
        self.num_processed_docs = 0
        if self.driver_batch_size:
            self.num_docs_in_same_request = num_docs_in_same_request
            self.total_batches_in_request = int(self.num_docs_in_same_request / self.driver_batch_size)
            self.total_num_docs = total_num_docs
            self.total_num_requests = self.total_num_docs / self.num_docs_in_same_request
            self.request_id = 0

    @property
    def total_documents_left_to_process(self):
        return self.total_num_docs - self.num_processed_docs

    @property
    def left_to_run_in_request(self):
        return self.num_docs_in_same_request - self.num_processed_in_request

    @property
    def num_processed_in_request(self):
        return self.num_processed_docs % ((self.request_id + 1) * self.num_docs_in_same_request)

    @property
    def next_expected_driver_batch_size(self):
        if not self.driver_batch_size:
            return None
        else:
            if self.left_to_run_in_request >= self.driver_batch_size:
                return min(self.driver_batch_size, self.total_documents_left_to_process)
            else:
                return min(self.left_to_run_in_request, self.total_documents_left_to_process)

    def encode(self, data: Any, *args, **kwargs) -> Any:
        assert len(data) == self.next_expected_driver_batch_size
        self.num_processed_docs += len(data)
        if self.num_processed_in_request > self.num_docs_in_same_request:
            self.request_id += 1
        return data


def document_generator(num_docs, num_chunks, num_chunks_chunks):
    for idx in range(num_docs):
        doc = Document(content=np.array([idx]))
        for chunk_idx in range(num_chunks):
            chunk = Document(content=np.array([chunk_idx]))
            for chunk_chunk_idx in range(num_chunks_chunks):
                chunk_chunk = Document(content=np.array([chunk_chunk_idx]))
                chunk.chunks.append(chunk_chunk)
            doc.chunks.append(chunk)
        yield doc


@pytest.mark.parametrize('request_batch_size', [5, 100, 500])
@pytest.mark.parametrize('driver_batch_size', [8, 16, 64])
def test_encode_driver_batching(request_batch_size, driver_batch_size, tmpdir):
    num_docs = 1315
    num_chunks = 0
    num_chunks_chunks = 0

    num_requests = int(num_docs / request_batch_size)
    num_docs_last_req_batch = num_docs % (num_requests * request_batch_size)

    def validate_response(resp):
        valid_resp_length = (len(resp.search.docs) == request_batch_size) or (
                    len(resp.search.docs) == num_docs_last_req_batch)
        assert valid_resp_length
        for doc in resp.search.docs:
            assert NdArray(doc.embedding).value is not None

    def fail_if_error(resp):
        assert False

    encoder = MockEncoder(driver_batch_size=driver_batch_size,
                          num_docs_in_same_request=request_batch_size,
                          total_num_docs=num_docs)

    driver = EncodeDriver(batch_size=driver_batch_size,
                          traversal_paths=('r',))

    encoder._drivers.clear()
    encoder._drivers['SearchRequest'] = [driver]

    executor_yml_file = os.path.join(tmpdir, 'executor.yml')
    encoder.save_config(executor_yml_file)

    with Flow().add(uses=executor_yml_file) as f:
        f.search(input_fn=document_generator(num_docs, num_chunks, num_chunks_chunks),
                 batch_size=request_batch_size,
                 on_done=validate_response,
                 on_error=fail_if_error)


@pytest.mark.parametrize('request_batch_size', [5, 100, 500])
@pytest.mark.parametrize('driver_batch_size', [8, 64, 128])
@pytest.mark.parametrize('num_chunks', [2, 8])
@pytest.mark.parametrize('num_chunks_chunks', [2, 8])
def test_encode_driver_batching_with_chunks(request_batch_size, driver_batch_size, num_chunks, num_chunks_chunks,
                                            tmpdir):
    num_docs = 1315
    num_requests = int(num_docs / request_batch_size)
    num_docs_last_req_batch = num_docs % (num_requests * request_batch_size)

    def validate_response(resp):
        valid_resp_length = (len(resp.search.docs) == request_batch_size) or (
                    len(resp.search.docs) == num_docs_last_req_batch)
        assert valid_resp_length
        for doc in resp.search.docs:
            assert NdArray(doc.embedding).value is not None
            for chunk in doc.chunks:
                assert NdArray(chunk.embedding).value is not None
                for chunk_chunk in chunk.chunks:
                    assert NdArray(chunk_chunk.embedding).value is not None

    def fail_if_error(resp):
        assert False

    encoder = MockEncoder(driver_batch_size=driver_batch_size,
                          num_docs_in_same_request=request_batch_size + request_batch_size*num_chunks + request_batch_size*num_chunks*num_chunks_chunks,
                          total_num_docs=num_docs + num_docs*num_chunks + num_docs*num_chunks*num_chunks_chunks)

    driver = EncodeDriver(batch_size=driver_batch_size,
                          traversal_paths=('r', 'c', 'cc'))

    encoder._drivers.clear()
    encoder._drivers['SearchRequest'] = [driver]

    executor_yml_file = os.path.join(tmpdir, 'executor.yml')
    encoder.save_config(executor_yml_file)

    with Flow().add(uses=executor_yml_file) as f:
        f.search(input_fn=document_generator(num_docs, num_chunks, num_chunks_chunks),
                 batch_size=request_batch_size,
                 on_done=validate_response,
                 on_error=fail_if_error)
