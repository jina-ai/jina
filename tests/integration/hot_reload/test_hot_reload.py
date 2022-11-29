import os
import time
import shutil
import contextlib

from jina import Flow, DocumentArray

cur_dir = os.path.dirname(os.path.abspath(__file__))


@contextlib.contextmanager
def _update_file(input_file_path, output_file_path, temp_path):
    backup_file = os.path.join(temp_path, 'backup.py')
    try:
        shutil.copy2(output_file_path, backup_file)
        shutil.copy(input_file_path, output_file_path)
        time.sleep(0.5)
        yield
    finally:
        shutil.copy2(backup_file, output_file_path)
        time.sleep(0.5)


def test_reload_simple_executor(tmpdir):
    from tests.integration.hot_reload.exec1.my_executor1 import MyExecutorToReload1

    f = Flow().add(uses=MyExecutorToReload1, hot_reload=True)
    with f:
        res = f.post(on='/', inputs=DocumentArray.empty(10))
        assert len(res) == 10
        for doc in res:
            assert doc.text == 'MyExecutorBeforeReload'
        with _update_file(os.path.join(cur_dir, 'my_executor_1_new.py'), os.path.join(cur_dir, 'exec1/my_executor1.py'),
                          str(tmpdir)):
            res = f.post(on='/', inputs=DocumentArray.empty(10))
            assert len(res) == 10
            for doc in res:
                assert doc.text == 'MyExecutorAfterReload'
        res = f.post(on='/', inputs=DocumentArray.empty(10))
        assert len(res) == 10
        for doc in res:
            assert doc.text == 'MyExecutorBeforeReload'


def test_reload_helper(tmpdir):
    from tests.integration.hot_reload.exec2.my_executor2 import MyExecutorToReload2

    f = Flow().add(uses=MyExecutorToReload2, hot_reload=True)
    with f:
        res = f.post(on='/', inputs=DocumentArray.empty(10))
        assert len(res) == 10
        for doc in res:
            assert doc.text == 'MyExecutorBeforeReload'
        with _update_file(os.path.join(cur_dir, 'helper2.py'), os.path.join(cur_dir, 'exec2/helper.py'),
                          str(tmpdir)):
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

    f = Flow().add(uses=A, hot_reload=True)
    with f:
        res = f.post(on='/', inputs=DocumentArray.empty(10))
        assert len(res) == 10
        for doc in res:
            assert doc.text == 'ABeforeReload'
        with _update_file(os.path.join(cur_dir, 'my_executor_3_new.py'), os.path.join(cur_dir, 'exec3/my_executor3.py'),
                          str(tmpdir)):
            res = f.post(on='/', inputs=DocumentArray.empty(10))
            assert len(res) == 10
            for doc in res:
                assert doc.text == 'AAfterReload'
        res = f.post(on='/', inputs=DocumentArray.empty(10))
        assert len(res) == 10
        for doc in res:
            assert doc.text == 'ABeforeReload'