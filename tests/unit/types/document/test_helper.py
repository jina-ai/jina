import types

import pytest

from jina import Document
from jina.types.document.helper import DocGroundtruthPair

@pytest.fixture(scope='function')
def document_factory():
    class DocumentFactory(object):
        def create(self, content):
            with Document() as d:
                d.content = content
            return d

    return DocumentFactory()

@pytest.fixture(scope='function')
def chunks(document_factory):
    return [
        document_factory.create('test chunk 1'),
        document_factory.create('test chunk 2'),
        document_factory.create('test chunk 3'),
    ]

@pytest.fixture(scope='function')
def matches(document_factory):
    return [
        document_factory.create('test match 1'),
        document_factory.create('test match 2'),
        document_factory.create('test match 3'),
    ]

@pytest.fixture(scope='function')
def document(document_factory, chunks, matches):
    doc = document_factory.create('test document')
    doc.chunks.extend(chunks)
    doc.matches.extend(matches)
    return doc

@pytest.fixture(scope='function')
def groundtruth(document_factory, chunks, matches):
    gt = document_factory.create('test groundtruth')
    gt.chunks.extend(chunks)
    gt.matches.extend(matches)
    return gt

def test_init(document, groundtruth):
    assert DocGroundtruthPair(doc=document, groundtruth=groundtruth)

def test_matches_success(document, groundtruth):
    pair = DocGroundtruthPair(doc=document, groundtruth=groundtruth)
    assert isinstance(pair.matches, types.GeneratorType)
    for _ in pair.matches:
        pass

def test_matches_fail(document_factory, document, groundtruth):
    # document and groundtruth not the same length
    groundtruth.matches.append(document_factory.create('test match 4'))
    pair = DocGroundtruthPair(doc=document, groundtruth=groundtruth)
    with pytest.raises(AssertionError):
        for _ in pair.matches:
            pass

def test_chunks_success(document, groundtruth):
    pair = DocGroundtruthPair(doc=document, groundtruth=groundtruth)
    assert isinstance(pair.chunks, types.GeneratorType)
    for _ in pair.chunks:
        pass

def test_chunks_fail(document_factory, document, groundtruth):
    # document and groundtruth not the same length
    groundtruth.chunks.append(document_factory.create('test chunk 4'))
    pair = DocGroundtruthPair(doc=document, groundtruth=groundtruth)
    with pytest.raises(AssertionError):
        for _ in pair.chunks:
            pass
