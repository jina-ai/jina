from jina import Document, DocumentArray, FaissIndexer
import numpy as np

import pytest


@pytest.fixture(scope='function')
def document_factory():
	class DocumentFactory(object):
		@staticmethod
		def create(idx, text, embedding):
			return Document(tags={'id': idx}, text=text, embedding=embedding)

	return DocumentFactory()

@pytest.fixture
def pool(document_factory):
	return [
        document_factory.create(1, 'pool 1', np.array([0.5, -1.0, 2.1]).astype('float32')),
        document_factory.create(2, 'pool 2', np.array([0.7, 1.0, 0.2]).astype('float32')),
        document_factory.create(3, 'pool 3', np.array([0.0, 0.0, 0.0]).astype('float32')),
    ]

@pytest.fixture
def queries(document_factory):
	return [
        document_factory.create(1, 'query 1', np.array([0.8, 0.8, 0.8]).astype('float32')),
        document_factory.create(2, 'query 2', np.array([0.5, -1.0, 2.1]).astype('float32')),
        document_factory.create(3, 'query 3', np.array([0.1, 0.1, 0.1]).astype('float32')),
    ]

def test_length(pool):
	container = FaissIndexer()
	assert len(container) == 0
	darray    = DocumentArray(pool)
	container = FaissIndexer(DocumentArray(pool))
	assert len(container) == len(darray)

def test_append(pool):
	container = FaissIndexer()
	for idx, doc in enumerate(pool):
		container.append(doc)
		assert len(container) == idx+1
	docs = [doc for doc in container]
	assert len(docs) == len(container)

def test_extend(pool):
	container = FaissIndexer()
	container.extend(pool)
	assert len(container) == len(pool)
	container.extend(pool)
	assert len(container) == 2*len(pool)

def test_search(pool, queries):
	container = FaissIndexer(DocumentArray(pool), use_for_metric='cosine')
	q 		  = DocumentArray(queries)
	q.match(container)
	dist, idx = container.search(query=q.embeddings, k=1)
	print(dist)
	print(idx)
	assert dist[1][0] == 0.

def test_embedding_size(pool):
	container = FaissIndexer(DocumentArray(pool))
	assert container.embeddings_size == 3

