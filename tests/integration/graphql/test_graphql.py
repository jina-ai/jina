from typing import Dict

import numpy as np
import pytest
from docarray.array.document import DocumentArray
from docarray.document import Document
from jina import Executor, Flow, requests
from sgqlc.endpoint.http import HTTPEndpoint

PORT_EXPOSE = 53171


class Indexer(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._docs = DocumentArray()

    @requests(on='/index')
    def index(self, docs: DocumentArray, **kwargs):
        self._docs.extend(docs)

    @requests(on='/search')
    def process(self, docs: DocumentArray, parameters: Dict, **kwargs):
        limit = 2
        if parameters:
            limit = int(parameters.get('limit', 2))
        docs.match(self._docs, limit=limit)


class Encoder(Executor):
    @requests
    def embed(self, docs: DocumentArray, **kwargs):
        docs.embeddings = np.random.random([len(docs), 10]).astype(np.float32)


@pytest.fixture(scope="module", autouse=True)
def flow():
    f = (
        Flow(protocol='http', port_expose=PORT_EXPOSE)
        .add(uses=Encoder)
        .add(uses=Indexer)
    )
    with f:
        f.index(inputs=(Document(text=t.strip()) for t in open(__file__) if t.strip()))
        yield


def graphql_query(query):
    return HTTPEndpoint(url=f'http://localhost:{PORT_EXPOSE}/graphql')(query=query)


@pytest.mark.parametrize('req_type', ['mutation', 'query'])
def test_id_only(req_type):
    response = graphql_query(
        '''
        %s {
            docs(body: {data: {text: "abcd"}}) { 
                id 
            } 
        }
    '''
        % req_type
    )
    assert 'data' in response
    assert 'docs' in response['data']
    assert len(response['data']['docs']) == 1
    assert set(response['data']['docs'][0].keys()) == {'id'}


@pytest.mark.parametrize('req_type', ['mutation', 'query'])
def test_id_and_text(req_type):
    response = graphql_query(
        '''
        %s {
            docs(body: {data: {text: "abcd"}}) { 
                id 
                text
            } 
        }
    '''
        % req_type
    )
    assert sorted(set(response['data']['docs'][0].keys())) == sorted({'id', 'text'})


@pytest.mark.parametrize('req_type', ['mutation', 'query'])
def test_id_in_matches(req_type):
    response = graphql_query(
        '''
        %s {
            docs(body: {data: {text: "abcd"}}) { 
                id 
                text
                matches {
                    id
                }
            } 
        }
    '''
        % req_type
    )
    assert sorted(set(response['data']['docs'][0].keys())) == sorted(
        {'id', 'text', 'matches'}
    )
    assert len(response['data']['docs'][0]['matches']) == 2
    for match in response['data']['docs'][0]['matches']:
        assert set(match.keys()) == {'id'}


@pytest.mark.parametrize('req_type', ['mutation', 'query'])
def test_id_text_in_matches(req_type):
    response = graphql_query(
        '''
        %s {
            docs(body: {data: {text: "abcd"}}) { 
                id 
                text
                matches {
                    id
                    text
                }
            } 
        }
    '''
        % req_type
    )
    assert sorted(set(response['data']['docs'][0].keys())) == sorted(
        {'id', 'text', 'matches'}
    )
    for match in response['data']['docs'][0]['matches']:
        assert sorted(set(match.keys())) == sorted({'id', 'text'})


@pytest.mark.parametrize('req_type', ['mutation', 'query'])
def test_text_scores_in_matches(req_type):
    response = graphql_query(
        '''
        %s {
            docs(body: {data: {text: "abcd"}}) { 
                id 
                text
                matches {
                    text
                    scores {
                        name
                        score {
                            value
                        }
                    }
                }
            } 
        }
    '''
        % req_type
    )
    assert sorted(set(response['data']['docs'][0].keys())) == sorted(
        {'id', 'text', 'matches'}
    )
    for match in response['data']['docs'][0]['matches']:
        assert sorted(set(match.keys())) == sorted({'text', 'scores'})
        assert match['scores'][0]['name'] == 'cosine'
        assert isinstance(match['scores'][0]['score']['value'], float)


@pytest.mark.parametrize('req_type', ['mutation', 'query'])
@pytest.mark.skip('Something wrong with json syntax is python string. Works on browser')
def test_parameters(req_type):
    response = graphql_query(
        '''
        %s {
            docs(body: {data: {text: "abcd"}, parameters: "{\"limit\": 3}"}) {
                id
                text
                matches {
                    text
                }
            }
        }
    '''
        % req_type
    )
    assert sorted(set(response['data']['docs'][0].keys())) == sorted(
        {'id', 'text', 'matches'}
    )
    assert len(response['data']['docs'][0]['matches']) == 3
