import contextlib
import os
import shutil
import time

from jina import DocumentArray, Flow

cur_dir = os.path.dirname(os.path.abspath(__file__))


@contextlib.contextmanager
def _update_file(input_file_path, output_file_path, temp_path):
    backup_file = os.path.join(temp_path, 'backup.py')
    try:
        shutil.copy2(output_file_path, backup_file)
        shutil.copy(input_file_path, output_file_path)
        time.sleep(2.0)
        yield
    finally:
        shutil.copy2(backup_file, output_file_path)
        time.sleep(2.0)


def test_reload_simple_executor(tmpdir):
    from tests.integration.hot_reload.exec1.my_executor1 import MyExecutorToReload1

    f = Flow().add(uses=MyExecutorToReload1, reload=True)
    with f:
        res = f.post(on='/', inputs=DocumentArray.empty(10))
        assert len(res) == 10
        for doc in res:
            assert doc.text == 'MyExecutorBeforeReload'
        with _update_file(
            os.path.join(cur_dir, 'my_executor_1_new.py'),
            os.path.join(cur_dir, 'exec1/my_executor1.py'),
            str(tmpdir),
        ):
            res = f.post(on='/', inputs=DocumentArray.empty(10))
            assert len(res) == 10
            for doc in res:
                assert doc.text == 'MyExecutorAfterReload'
        res = f.post(on='/', inputs=DocumentArray.empty(10))
        assert len(res) == 10
        for doc in res:
            assert doc.text == 'MyExecutorBeforeReload'


def test_reload_with_dynamic_batching(tmpdir):
    from tests.integration.hot_reload.exec1.my_executor1 import MyExecutorToReload1

    f = Flow().add(
        uses=MyExecutorToReload1,
        reload=True,
        uses_dynamic_batching={'/bar': {'preferred_batch_size': 1, 'timeout': 1000}},
    )
    with f:
        res = f.post(on='/bar', inputs=DocumentArray.empty(10))
        assert len(res) == 10
        for doc in res:
            assert doc.text == 'MyExecutorBeforeReloadBar'
        with _update_file(
            os.path.join(cur_dir, 'my_executor_1_new.py'),
            os.path.join(cur_dir, 'exec1/my_executor1.py'),
            str(tmpdir),
        ):
            res = f.post(on='/bar', inputs=DocumentArray.empty(10))
            assert len(res) == 10
            for doc in res:
                assert doc.text == 'MyExecutorAfterReloadBar'
        res = f.post(on='/bar', inputs=DocumentArray.empty(10))
        assert len(res) == 10
        for doc in res:
            assert doc.text == 'MyExecutorBeforeReloadBar'


def test_reload_helper(tmpdir):
    from tests.integration.hot_reload.exec2.my_executor2 import MyExecutorToReload2

    f = Flow().add(uses=MyExecutorToReload2, reload=True)
    with f:
        res = f.post(on='/', inputs=DocumentArray.empty(10))
        assert len(res) == 10
        for doc in res:
            assert doc.text == 'MyExecutorBeforeReload'
        with _update_file(
            os.path.join(cur_dir, 'helper2.py'),
            os.path.join(cur_dir, 'exec2/helper.py'),
            str(tmpdir),
        ):
            res = f.post(on='/', inputs=DocumentArray.empty(10))
            assert len(res) == 10
            for doc in res:
                assert doc.text == 'MyExecutorAfterReload'
        res = f.post(on='/', inputs=DocumentArray.empty(10))
        assert len(res) == 10
        for doc in res:
            assert doc.text == 'MyExecutorBeforeReload'


def test_reload_with_inheritance(tmpdir):
    from tests.integration.hot_reload.exec3.my_executor3 import A, EnhancedExecutor

    f = Flow().add(uses=A, reload=True)
    with f:
        res = f.post(on='/', inputs=DocumentArray.empty(10))
        assert len(res) == 10
        for doc in res:
            assert doc.text == 'ABeforeReload'
        with _update_file(
            os.path.join(cur_dir, 'my_executor_3_new.py'),
            os.path.join(cur_dir, 'exec3/my_executor3.py'),
            str(tmpdir),
        ):
            res = f.post(on='/', inputs=DocumentArray.empty(10))
            assert len(res) == 10
            for doc in res:
                assert doc.text == 'AAfterReload'
        res = f.post(on='/', inputs=DocumentArray.empty(10))
        assert len(res) == 10
        for doc in res:
            assert doc.text == 'ABeforeReload'


def test_reload_from_config(tmpdir):
    f = Flow().add(uses=os.path.join(cur_dir, os.path.join('exec4', 'config.yml')), reload=True)
    with f:
        res = f.post(on='/', inputs=DocumentArray.empty(10))
        assert len(res) == 10
        for doc in res:
            assert doc.text == 'MyExecutorBeforeReload'
        with _update_file(
                os.path.join(cur_dir, 'my_executor_4_new.py'),
                os.path.join(cur_dir, 'exec4/my_executor4.py'),
                str(tmpdir),
        ):
            res = f.post(on='/', inputs=DocumentArray.empty(10))
            assert len(res) == 10
            for doc in res:
                assert doc.text == 'MyExecutorAfterReload'
        res = f.post(on='/', inputs=DocumentArray.empty(10))
        assert len(res) == 10
        for doc in res:
            assert doc.text == 'MyExecutorBeforeReload'