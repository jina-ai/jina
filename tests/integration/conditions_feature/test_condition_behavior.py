import os

import pytest
from docarray import Document, DocumentArray

from jina import Executor, Flow, requests

cur_dir = os.path.dirname(os.path.abspath(__file__))


class ConditionDumpExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        with open(
            os.path.join(str(self.workspace), f'{self.metas.name}.txt'), 'w', encoding='utf-8'
        ) as fp:
            for doc in docs:
                fp.write(doc.text)
                doc.text += f' processed by {self.metas.name}'


@pytest.fixture()
def temp_workspace(tmpdir):
    os.environ['TEMP_WORKSPACE'] = str(tmpdir)
    yield
    os.unsetenv('TEMP_WORKSPACE')


@pytest.fixture
def shuffle_flow(request, temp_workspace):
    f = (
        Flow()
        .add(name='first')
        .add(
            uses=ConditionDumpExecutor,
            uses_metas={'name': 'exec1'},
            workspace=os.environ['TEMP_WORKSPACE'],
            name='exec1',
            needs=['first'],
            when={
                '$or': {
                    'tags__third': {'$eq': 1},
                    'tags__first': {'$eq': 1},
                    'tags__fourth': {'$eq': 1},
                }
            },
        )
        .add(
            uses=ConditionDumpExecutor,
            uses_metas={'name': 'exec2'},
            name='exec2',
            workspace=os.environ['TEMP_WORKSPACE'],
            needs='first',
            when={'$or': {'tags__second': {'$eq': 1}, 'tags__fifth': {'$eq': 1}}},
        )
        .needs_all('joiner')
    )
    return f


@pytest.fixture
def flow(request, temp_workspace):
    source = request.param
    if source == 'python':
        f = (
            Flow()
            .add(name='first')
            .add(
                uses=ConditionDumpExecutor,
                uses_metas={'name': 'exec1'},
                workspace=os.environ['TEMP_WORKSPACE'],
                name='exec1',
                needs=['first'],
                when={'tags__type': {'$eq': 1}},
            )
            .add(
                uses=ConditionDumpExecutor,
                workspace=os.environ['TEMP_WORKSPACE'],
                uses_metas={'name': 'exec2'},
                name='exec2',
                needs='first',
                when={'tags__type': {'$gt': 1}},
            )
            .needs_all('joiner')
        )
    else:
        f = Flow.load_config(os.path.join(cur_dir, 'flow.yml'))
    return f


@pytest.mark.parametrize('flow', ['python', 'yaml'], indirect=True)
def test_conditions_filtering(tmpdir, flow):
    with flow:
        ret = flow.post(
            on='index',
            inputs=DocumentArray(
                [
                    Document(text='type1', tags={'type': 1}),
                    Document(text='type2', tags={'type': 2}),
                ]
            ),
        )
        assert len(ret) == 2
        types_set = set()
        for doc in ret:
            if doc.tags['type'] == 1:
                assert doc.text == 'type1 processed by exec1'
            else:
                assert doc.tags['type'] == 2
                assert doc.text == 'type2 processed by exec2'
            types_set.add(doc.tags['type'])

        assert types_set == {1, 2}

    with open(os.path.join(str(tmpdir), 'exec1', '0', f'exec1.txt'), 'r', encoding='utf-8') as fp:
        assert fp.read() == 'type1'

    with open(os.path.join(str(tmpdir), 'exec2', '0', f'exec2.txt'), 'r', encoding='utf-8') as fp:
        assert fp.read() == 'type2'


def test_conditions_filtering_on_joiner(tmpdir):
    flow = (
        Flow()
        .add(name='first')
        .add(
            uses=ConditionDumpExecutor,
            uses_metas={'name': 'joiner_test_exec1'},
            workspace=str(tmpdir),
            name='joiner_test_exec1',
            needs=['first'],
        )
        .add(
            uses=ConditionDumpExecutor,
            workspace=str(tmpdir),
            uses_metas={'name': 'joiner_test_exec2'},
            name='joiner_test_exec2',
            needs='first',
        )
        .needs_all('joiner', when={'tags__type': {'$eq': 3}})
    )
    with flow:
        ret = flow.post(
            on='index',
            inputs=DocumentArray(
                [
                    Document(text='type1', tags={'type': 1}),
                    Document(text='type2', tags={'type': 2}),
                ]
            ),
        )
        assert len(ret) == 0

    with open(
        os.path.join(str(tmpdir), 'joiner_test_exec1', '0', f'joiner_test_exec1.txt'),
        'r', encoding='utf-8',
    ) as fp:
        assert fp.read() == 'type1type2'

    with open(
        os.path.join(str(tmpdir), 'joiner_test_exec2', '0', f'joiner_test_exec2.txt'),
        'r', encoding='utf-8',
    ) as fp:
        assert fp.read() == 'type1type2'


def test_sorted_response(tmpdir, shuffle_flow):
    tag_list = ['first', 'second', 'third', 'fourth', 'fifth']
    inputs = DocumentArray.empty(6)
    for i in range(5):  # no tag for last doc
        inputs[i].tags[tag_list[i]] = 1  # one-hot encoding

    with shuffle_flow as f:
        ret = f.post(on='/index', inputs=inputs)

    assert len(ret) == 5

    for i, doc in enumerate(ret):
        assert doc.tags[tag_list[i]] == 1

    inputs = inputs[:5]
    for og, returned in zip(inputs, ret):
        assert og.id == returned.id


def test_chained_conditions(tmpdir, temp_workspace):
    f = (
        Flow()
        .add(name='first')
        .add(
            uses=ConditionDumpExecutor,
            uses_metas={'name': 'exec1'},
            workspace=os.environ['TEMP_WORKSPACE'],
            name='exec1',
            needs=['first'],
            when={'tags__type': {'$gte': 2}},
        )
        .add(
            uses=ConditionDumpExecutor,
            workspace=os.environ['TEMP_WORKSPACE'],
            uses_metas={'name': 'exec2'},
            name='exec2',
            needs='exec1',
            when={'tags__type': {'$lte': 1}},
        )
        .needs_all('joiner')
    )

    with f:
        ret = f.post(
            on='index',
            inputs=DocumentArray(
                [
                    Document(text='type1', tags={'type': 1}),
                    Document(text='type2', tags={'type': 2}),
                    Document(text='type2', tags={'type': 3}),
                ]
            ),
        )
        assert len(ret) == 0
