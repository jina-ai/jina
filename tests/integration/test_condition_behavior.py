import os

from docarray import DocumentArray, Document
from jina import Executor, Flow, requests


def test_conditions_filtering(tmpdir):
    class DumpExecutor(Executor):
        @requests
        def foo(self, docs, **kwargs):
            with open(
                os.path.join(str(self.workspace), f'{self.metas.name}.txt'), 'w'
            ) as fp:
                for doc in docs:
                    fp.write(doc.text)
                    doc.text += f' processed by {self.metas.name}'

    f = (
        Flow()
        .add(name='first')
        .add(
            uses=DumpExecutor,
            uses_metas={'name': 'exec1'},
            workspace=str(tmpdir),
            name='exec1',
            needs='first',
            condition={'type': '1'},
        )
        .add(
            uses=DumpExecutor,
            workspace=str(tmpdir),
            uses_metas={'name': 'exec2'},
            name='exec2',
            needs='first',
            condition={'type': '2'},
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
