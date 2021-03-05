import os
from typing import List, Dict

import numpy as np
import pytest

from jina import Document
from jina.executors.segmenters import BaseSegmenter
from jina.executors.encoders import BaseEncoder
from jina.flow import Flow

from tests import validate_callback

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='function')
def docs():
    documents = []
    for i in range(1, 4):
        with Document() as doc:
            doc.text = (
                f'title: this is mode1 from doc{i}, body: this is mode2 from doc{i}'
            )
        documents.append(doc)
    return documents


class MockSegmenterReduce(BaseSegmenter):
    def segment(self, text: str, *args, **kwargs) -> List[Dict]:
        split = text.split(',')
        chunks = [
            dict(text=split[0], offset=0, weight=1.0, modality='mode1'),
            dict(text=split[1], offset=1, weight=1.0, modality='mode2'),
        ]
        return chunks


class MockEncoderReduce(BaseEncoder):
    def encode(self, data: str, *args, **kwargs) -> 'np.ndarray':
        output = []
        for r in data:
            if 'mode1' in r:
                output.append([0.0, 0.0, 0.0])
            elif 'mode2' in r:
                output.append([1.0, 1.0, 1.0])

        return np.array(output)


def test_merge_chunks_with_different_modality(mocker, docs):
    def input_function():
        return docs

    def validate(req):
        assert len(req.index.docs) == 3
        for doc in req.index.docs:
            assert len(doc.chunks) == 2
            assert doc.chunks[0].modality in ['mode1', 'mode2']
            assert doc.chunks[1].modality in ['mode1', 'mode2']
            assert doc.chunks[0].modality != doc.chunks[1].modality

    response_mock = mocker.Mock()

    flow = (
        Flow()
        .add(name='segmenter', uses='MockSegmenterReduce')
        .add(name='encoder1', uses=os.path.join(cur_dir, 'yaml/mockencoder-mode1.yml'))
        .add(
            name='encoder2',
            uses=os.path.join(cur_dir, 'yaml/mockencoder-mode2.yml'),
            needs=['segmenter'],
        )
        .add(
            name='reducer',
            uses='- !ReduceAllDriver | {traversal_paths: [c]}',
            needs=['encoder1', 'encoder2'],
        )
    )

    with flow:
        flow.index(inputs=input_function, on_done=response_mock)

    validate_callback(response_mock, validate)


def test_reduce_all_root_chunks(mocker, docs):
    def input_fn():
        return docs

    def validate(req):
        assert len(req.index.docs) == 6
        for doc in req.index.docs:
            assert len(doc.chunks) == 1
            assert doc.chunks[0].modality in ['mode1', 'mode2']

    response_mock = mocker.Mock()

    flow = (
        Flow()
        .add(name='segmenter', uses='MockSegmenterReduce')
        .add(name='encoder1', uses=os.path.join(cur_dir, 'yaml/mockencoder-mode1.yml'))
        .add(
            name='encoder2',
            uses=os.path.join(cur_dir, 'yaml/mockencoder-mode2.yml'),
            needs=['segmenter'],
        )
        .add(
            name='reducer',
            uses='- !ReduceAllDriver | {traversal_paths: [r]}',
            needs=['encoder1', 'encoder2'],
        )
    )

    with flow:
        flow.index(input_fn=input_fn, on_done=response_mock)
    validate_callback(response_mock, validate)
