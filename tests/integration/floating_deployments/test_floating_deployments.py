import os
import time

import pytest

from jina import DocumentArray, Executor, Flow, __default_endpoint__, requests

TIME_SLEEP_FLOATING = 2


class FloatingTestExecutor(Executor):
    def __init__(self, file_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_name = file_name

    @requests
    def foo(self, docs, **kwargs):
        time.sleep(TIME_SLEEP_FLOATING)
        with open(self.file_name, 'a+') as f:
            f.write('here ')

        for d in docs:
            d.text = 'change it'


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_floating_executors(tmpdir, protocol):
    NUM_REQ = 20
    file_name = os.path.join(str(tmpdir), 'file.txt')
    expected_str = 'here ' * NUM_REQ

    f = (
        Flow(protocol=protocol)
        .add(name='first')
        .add(
            name='second',
            floating=True,
            uses=FloatingTestExecutor,
            uses_with={'file_name': file_name},
        )
    )

    with f:
        for j in range(NUM_REQ):
            start_time = time.time()
            ret = f.post(on=__default_endpoint__, inputs=DocumentArray.empty(1))
            end_time = time.time()
            assert (
                end_time - start_time
            ) < TIME_SLEEP_FLOATING  # check that the response arrives before the
            # Floating Executor finishes
            assert len(ret) == 1
            assert ret[0].text == ''

    with open(file_name, 'r') as f:
        resulted_str = f.read()

    assert resulted_str == expected_str


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_floating_executors_right_after_gateway(tmpdir, protocol):
    NUM_REQ = 20
    file_name = os.path.join(str(tmpdir), 'file.txt')
    expected_str = 'here ' * NUM_REQ

    f = (
        Flow(protocol=protocol)
        .add(name='first')
        .add(
            name='second',
            floating=True,
            uses=FloatingTestExecutor,
            uses_with={'file_name': file_name},
            needs=['gateway'],
        )
    )

    with f:
        for j in range(NUM_REQ):
            start_time = time.time()
            ret = f.post(on=__default_endpoint__, inputs=DocumentArray.empty(1))
            end_time = time.time()
            assert (
                end_time - start_time
            ) < TIME_SLEEP_FLOATING  # check that the response arrives before the
            # Floating Executor finishes
            assert len(ret) == 1
            assert ret[0].text == ''

    with open(file_name, 'r') as f:
        resulted_str = f.read()

    assert resulted_str == expected_str


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_multiple_floating_points(tmpdir, protocol):
    NUM_REQ = 20
    file_name1 = os.path.join(str(tmpdir), 'file1.txt')
    file_name2 = os.path.join(str(tmpdir), 'file2.txt')
    expected_str = 'here ' * NUM_REQ

    f = (
        Flow(protocol=protocol)
        .add(name='first')
        .add(
            name='second',
            floating=True,
            uses=FloatingTestExecutor,
            uses_with={'file_name': file_name1},
        )
        .add(
            name='third',
            floating=True,
            uses=FloatingTestExecutor,
            uses_with={'file_name': file_name2},
        )
    )

    with f:
        for j in range(NUM_REQ):
            start_time = time.time()
            ret = f.post(on=__default_endpoint__, inputs=DocumentArray.empty(1))
            end_time = time.time()
            assert (
                end_time - start_time
            ) < TIME_SLEEP_FLOATING  # check that the response arrives before the
            assert len(ret) == 1
            assert ret[0].text == ''

    with open(file_name1, 'r') as f:
        resulted_str = f.read()

    assert resulted_str == expected_str

    with open(file_name2, 'r') as f:
        resulted_str = f.read()

    assert resulted_str == expected_str


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_complex_flow(tmpdir, protocol):
    NUM_REQ = 20
    file_name1 = os.path.join(str(tmpdir), 'file1.txt')
    file_name2 = os.path.join(str(tmpdir), 'file2.txt')
    expected_str = 'here ' * NUM_REQ

    f = (
        Flow(protocol=protocol)
        .add(name='pod0')
        .add(name='pod4', needs=['gateway'])
        .add(
            name='floating_pod6',
            needs=['gateway'],
            floating=True,
            uses=FloatingTestExecutor,
            uses_with={'file_name': file_name2},
        )
        .add(
            name='floating_pod1',
            needs=['pod0'],
            floating=True,
            uses=FloatingTestExecutor,
            uses_with={'file_name': file_name1},
        )
        .add(name='pod2', needs=['pod0'])
        .add(name='pod3', needs=['pod2'])
        .add(name='pod5', needs=['pod4'])
        .add(name='merger', needs=['pod5', 'pod3'])
        .add(name='pod_last', needs=['merger'])
    )

    with f:
        for j in range(NUM_REQ):
            start_time = time.time()
            ret = f.post(on=__default_endpoint__, inputs=DocumentArray.empty(1))
            end_time = time.time()
            assert (
                end_time - start_time
            ) < TIME_SLEEP_FLOATING  # check that the response arrives before the
            assert len(ret) == 1
            assert ret[0].text == ''

    with open(file_name1, 'r') as f:
        resulted_str = f.read()

    assert resulted_str == expected_str

    with open(file_name2, 'r') as f:
        resulted_str = f.read()

    assert resulted_str == expected_str


@pytest.mark.parametrize('needs', ['gateway', 'executor0'])
def test_floating_needs(needs):
    class FastChangingExecutor(Executor):
        @requests()
        def foo(self, docs, **kwargs):
            for doc in docs:
                doc.text = 'Hello World'

    class SlowChangingExecutor(Executor):
        @requests()
        def foo(self, docs, **kwargs):
            time.sleep(TIME_SLEEP_FLOATING)
            for doc in docs:
                doc.text = 'Change the document but will not affect response'

    f = (
        Flow()
        .add(name='executor0', uses=FastChangingExecutor)
        .add(
            name='floating_executor',
            uses=SlowChangingExecutor,
            needs=[needs],
            floating=True,
        )
    )
    with f:
        f.post(on='/endpoint', inputs=DocumentArray.empty(1))  # we need to send a first
        start_time = time.time()
        response = f.post(on='/endpoint', inputs=DocumentArray.empty(2))
        end_time = time.time()
        assert (end_time - start_time) < TIME_SLEEP_FLOATING
        assert response.texts == ['Hello World', 'Hello World']


@pytest.mark.parametrize('needs', ['gateway', 'executor0', 'executor1'])
def test_floating_needs_more_complex(needs):
    class FastChangingExecutor(Executor):
        @requests()
        def foo(self, docs, **kwargs):
            for doc in docs:
                doc.text = 'Hello World'

    class FastAddExecutor(Executor):
        @requests()
        def foo(self, docs, **kwargs):
            for doc in docs:
                doc.text += ' from FastAddExecutor'

    class SlowChangingExecutor(Executor):
        @requests()
        def foo(self, docs, **kwargs):
            time.sleep(TIME_SLEEP_FLOATING)
            for doc in docs:
                doc.text = 'Change the document but will not affect response'

    f = (
        Flow()
        .add(name='executor0', uses=FastChangingExecutor)
        .add(name='executor1', uses=FastAddExecutor, needs=['executor0'])
        .add(
            name='floating_executor',
            uses=SlowChangingExecutor,
            needs=[needs],
            floating=True,
        )
    )
    with f:
        f.post(on='/endpoint', inputs=DocumentArray.empty(1))  # we need to send a first
        start_time = time.time()
        response = f.post(on='/endpoint', inputs=DocumentArray.empty(2))
        end_time = time.time()
        assert (end_time - start_time) < TIME_SLEEP_FLOATING
        assert response.texts == [
            'Hello World from FastAddExecutor',
            'Hello World from FastAddExecutor',
        ]
