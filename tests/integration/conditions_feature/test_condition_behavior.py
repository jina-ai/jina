import os
import pytest

from docarray import DocumentArray, Document
from jina import Executor, Flow, requests

cur_dir = os.path.dirname(os.path.abspath(__file__))


class ContitionDumpExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        with open(
            os.path.join(str(self.workspace), f'{self.metas.name}.txt'), 'w'
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
def flow(request, temp_workspace):
    source = request.param
    if source == 'python':
        f = (
            Flow()
            .add(name='first')
            .add(
                uses=ContitionDumpExecutor,
                uses_metas={'name': 'exec1'},
                workspace=os.environ['TEMP_WORKSPACE'],
                name='exec1',
                needs='first',
                condition={'type': '1'},
            )
            .add(
                uses=ContitionDumpExecutor,
                workspace=os.environ['TEMP_WORKSPACE'],
                uses_metas={'name': 'exec2'},
                name='exec2',
                needs='first',
                condition={'type': '2'},
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

    with open(os.path.join(str(tmpdir), 'exec1', '0', f'exec1.txt'), 'r') as fp:
        assert fp.read() == 'type1'

    with open(os.path.join(str(tmpdir), 'exec2', '0', f'exec2.txt'), 'r') as fp:
        assert fp.read() == 'type2'
