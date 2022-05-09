import asyncio
import time
import urllib.error
from typing import Dict

import numpy as np
import pytest
from docarray.array.document import DocumentArray
from docarray.document import Document

from jina import Client, Executor, Flow, requests

PORT_EXPOSE = 53171
PORT_EXPOSE_NO_GRAPHQL = 53172
SLOW_EXEC_DELAY = 1


class GraphQLTestIndexer(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._docs = DocumentArray()

    @requests(on='/index')
    def index(self, docs: DocumentArray, **kwargs):
        self._docs.extend(docs)

    @requests(on='/search')
    def process(self, docs: DocumentArray, parameters: Dict, **kwargs):
        limit = int(parameters.get('limit', 2))
        docs.match(self._docs, limit=limit)

    @requests(on='/foo')
    def foo(self, docs: DocumentArray, **kwargs):
        docs[0].text = 'foo'

    @requests(on='/bar')
    def bar(self, docs: DocumentArray, **kwargs):
        docs[0].text = 'bar'

    @requests(on='/target-exec')
    def target_exec(self, docs: DocumentArray, **kwargs):
        docs[0].text = 'Indexer'


class SlowExec(Executor):
    @requests(on='/slow')
    def foo(self, docs: DocumentArray, **kwargs):
        time.sleep(SLOW_EXEC_DELAY)


class GraphQLTestEncoder(Executor):
    @requests
    def embed(self, docs: DocumentArray, **kwargs):
        docs.embeddings = np.random.random([len(docs), 10]).astype(np.float32)

    @requests(on='/target-exec')
    def target_exec(self, docs: DocumentArray, **kwargs):
        docs[0].text = 'Encoder'


@pytest.fixture(scope="module", autouse=True)
def flow():
    f = (
        Flow(protocol='http', port_expose=PORT_EXPOSE, expose_graphql_endpoint=True)
        .add(uses=GraphQLTestEncoder, name='Encoder')
        .add(uses=GraphQLTestIndexer, name='Indexer')
        .add(uses=SlowExec)
    )
    with f:
        f.index(inputs=(Document(text=t.strip()) for t in open(__file__) if t.strip()))
        yield


@pytest.fixture(scope="module", autouse=True)
def no_graphql_flow():
    f = (
        Flow(
            protocol='http',
            port_expose=PORT_EXPOSE_NO_GRAPHQL,
            expose_graphql_endpoint=False,
            cors=True,
            no_crud_endpoints=True,
        )
        .add(uses=GraphQLTestEncoder, name='Encoder')
        .add(uses=GraphQLTestIndexer, name='Indexer')
        .add(uses=SlowExec)
    )
    with f:
        f.index(inputs=(Document(text=t.strip()) for t in open(__file__) if t.strip()))
        yield


def graphql_query(mutation, use_nogql_flow=False):
    p = PORT_EXPOSE_NO_GRAPHQL if use_nogql_flow else PORT_EXPOSE
    c = Client(port=p, protocol='HTTP')
    return c.mutate(mutation=mutation)


async def async_graphql_query(mutation):
    c = Client(port=PORT_EXPOSE, protocol='HTTP', asyncio=True)
    return await c.mutate(mutation=mutation)


@pytest.mark.parametrize('req_type', ['mutation', 'query'])
def test_id_only(req_type):
    response = graphql_query(
        (
            f'{req_type} {{'
            '''docs(data: {text: "abcd"}) { 
                id 
            } 
        }
    '''
        )
    )
    assert 'data' in response
    assert 'docs' in response['data']
    assert len(response['data']['docs']) == 1
    assert set(response['data']['docs'][0].keys()) == {'id'}


@pytest.mark.parametrize('req_type', ['mutation', 'query'])
def test_asyncio(req_type, tmp_path):
    q = (
        f'{req_type} {{'
        '''docs(data: {text: "abcd"}, execEndpoint: "/slow") { 
                    id 
                } 
            }
        '''
    )

    local_delay = 2
    num_requests = 3

    async def slow_local_method():
        await asyncio.sleep(local_delay)

    async def concurrent_mutations():
        inputs = [async_graphql_query(q) for _ in range(num_requests)]
        inputs.append(slow_local_method())
        await asyncio.gather(*inputs)

    start = time.time()
    asyncio.run(concurrent_mutations())
    tot_time = time.time() - start

    assert (
        tot_time < local_delay + num_requests * SLOW_EXEC_DELAY
    )  # save time through asyncio


@pytest.mark.parametrize('req_type', ['mutation', 'query'])
def test_data_list(req_type):
    texts = 'abcd', 'efgh', 'ijkl'
    response = graphql_query(
        (
            f'{req_type} {{'
            f'docs(data: [{{text: "{texts[0]}"}}, {{text: "{texts[1]}"}}, {{text: "{texts[2]}"}}]) {{'
            '''text
            } 
        }
    '''
        )
    )
    assert 'data' in response
    assert 'docs' in response['data']
    assert len(response['data']['docs']) == 3
    assert response['data']['docs'][0]['text'] == texts[0]
    assert response['data']['docs'][1]['text'] == texts[1]
    assert response['data']['docs'][2]['text'] == texts[2]


@pytest.mark.parametrize('req_type', ['mutation', 'query'])
def test_id_and_text(req_type):
    response = graphql_query(
        (
            f'{req_type} {{'
            '''docs(data: {text: "abcd"}) { 
                id 
                text
            } 
        }
    '''
        )
    )
    assert sorted(set(response['data']['docs'][0].keys())) == sorted({'id', 'text'})


@pytest.mark.parametrize('req_type', ['mutation', 'query'])
def test_id_in_matches(req_type):
    response = graphql_query(
        (
            f'{req_type} {{'
            '''docs(data: {text: "abcd"}) { 
                id 
                text
                matches {
                    id
                }
            } 
        }
    '''
        )
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
        (
            f'{req_type} {{'
            '''docs(data: {text: "abcd"}) { 
                id 
                text
                matches {
                    id
                    text
                }
            } 
        }
    '''
        )
    )
    assert sorted(set(response['data']['docs'][0].keys())) == sorted(
        {'id', 'text', 'matches'}
    )
    for match in response['data']['docs'][0]['matches']:
        assert sorted(set(match.keys())) == sorted({'id', 'text'})


@pytest.mark.parametrize('req_type', ['mutation', 'query'])
def test_text_scores_in_matches(req_type):
    response = graphql_query(
        (
            f'{req_type} {{'
            '''docs(data: {text: "abcd"}) { 
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
        )
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
        (
            f'{req_type} {{'
            '''docs(data: {text: "abcd"}, parameters: "{\"limit\": 3}") {
                id
                text
                matches {
                    text
                }
            }
        }
    '''
        )
    )
    assert sorted(set(response['data']['docs'][0].keys())) == sorted(
        {'id', 'text', 'matches'}
    )
    assert len(response['data']['docs'][0]['matches']) == 3


@pytest.mark.parametrize('req_type', ['mutation', 'query'])
@pytest.mark.parametrize('endpoint', ['/foo', '/bar'])
def test_endpoints(req_type, endpoint):
    response_foo = graphql_query(
        (
            f'{req_type} {{'
            f'docs(data: {{text: "abcd"}}, execEndpoint: "{endpoint}") {{'
            '''text
            } 
        }
    '''
        )
    )

    assert 'data' in response_foo
    assert 'docs' in response_foo['data']
    assert 'text' in response_foo['data']['docs'][0]
    assert response_foo['data']['docs'][0]['text'] == endpoint[1:]


@pytest.mark.parametrize('req_type', ['mutation', 'query'])
@pytest.mark.parametrize('target', ['Indexer', 'Encoder'])
def test_target_exec(req_type, target):
    response_foo = graphql_query(
        (
            f'{req_type} {{'
            f'docs(data: {{text: "abcd"}}, targetExecutor: "{target}", execEndpoint: "/target-exec") {{'
            '''text
            } 
        }
    '''
        )
    )

    assert 'data' in response_foo
    assert 'docs' in response_foo['data']
    assert 'text' in response_foo['data']['docs'][0]
    assert response_foo['data']['docs'][0]['text'] == target


def test_disable_graphql_endpoint():
    with pytest.raises(ConnectionError) as err_info:
        response = graphql_query(
            (
                '''mutation {
                   docs(data: {text: "abcd"}) { 
                    id 
                } 
            }
        '''
            ),
            use_nogql_flow=True,
        )
    assert '404' in err_info.value.args[0]
