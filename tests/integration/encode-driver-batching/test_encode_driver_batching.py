from typing import Any

import pytest
import numpy as np

from jina.executors import BaseExecutor
from jina.executors.encoders import BaseEncoder
from jina.drivers.encode import EncodeDriver
from jina.flow import Flow
from jina import Document


class MockEncoder(BaseEncoder):
    def __init__(self,
                 driver_batch_size: int,
                 total_num_docs: int,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver_batch_size = driver_batch_size
        if self.driver_batch_size:
            self.total_num_docs = total_num_docs
            self.total_passes = int(self.total_num_docs / self.driver_batch_size)
            self.id_pass = 0

    @property
    def is_last_batch(self):
        return self.id_pass == self.total_passes

    def encode(self, data: Any, *args, **kwargs) -> Any:
        # encodes 10 * data into the encoder, so return data
        if self.driver_batch_size:
            if not self.is_last_batch:
                assert len(data) == self.driver_batch_size
            else:
                left_to_run_in_request = self.total_num_docs - (self.driver_batch_size * self.total_passes)
                assert len(data) == left_to_run_in_request
            self.id_pass += 1
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


@pytest.mark.parametrize('request_batch_size', [100, 200, 500])
@pytest.mark.parametrize('driver_batch_size',  [8, 64, 128])
@pytest.mark.parametrize('num_chunks',  [0, 8, 64, 64, 128])
@pytest.mark.parametrize('traversal_paths', [('rcc', 'cc')])
def test_encode_driver_batching(request_batch_size, driver_batch_size, num_chunks, traversal_paths, mocker):

    def validate_response(resp):
        assert len(resp.search.docs) == request_batch_size
        for doc in resp.search.docs:
            assert doc.embedding is not None

    num_docs = 6598
    num_chunks_chunks = 3
    encoder = MockEncoder(driver_batch_size=driver_batch_size, total_num_docs=num_docs)
    driver = EncodeDriver(batch_size=driver_batch_size,
                          traversal_paths=traversal_paths)

    encoder._drivers.clear()
    encoder._drivers['SearchRequest'] = driver

    yaml_repr = BaseExecutor._dump_instance_to_yaml(encoder)
    print(yaml_repr)

    response_mock = mocker.Mock(wrap=validate_response)

    with Flow().add(uses=yaml_repr) as f:
        f.search(input_fn=document_generator(num_docs, num_chunks, num_chunks_chunks), output_fn=response_mock)

    response_mock.assert_called()
