import os
import time

from jina import Document, DocumentArray, Executor, Flow, requests


def test_floating_points(tmpdir):
    NUM_REQ = 20
    file_name = os.path.join(str(tmpdir), 'file.txt')
    print(f' file_name {file_name}')
    expected_str = 'here ' * NUM_REQ

    class FloatingExecutor(Executor):
        @requests
        def foo(self, docs, **kwargs):
            time.sleep(0.5)
            with open(file_name, 'a+') as f:
                f.write('here ')

            for d in docs:
                d.text = 'change it'

    f = (
        Flow()
        .add(name='first')
        .add(name='second', floating=True, uses=FloatingExecutor)
    )

    with f:
        for j in range(NUM_REQ):
            ret = f.post(on='/default', inputs=DocumentArray.empty(1))
            assert len(ret) == 1
            assert ret[0].text == ''
            time.sleep(0.1)

    with open(file_name, 'r') as f:
        resulted_str = f.read()

    assert resulted_str == expected_str
