import numpy as np
import pytest

from jina import DocumentArray, Document
from jina.drivers.encode import EncodeDriver
from jina.executors.encoders import BaseEncoder
from tests import random_docs


def test_extract_multi_fields(mocker):
    encode_mock = mocker.Mock()

    class MyExecutor(BaseEncoder):
        def encode(self, id, embedding):
            encode_mock()
            assert isinstance(id, list)
            assert isinstance(embedding, list)
            assert isinstance(id[0], str)
            assert isinstance(embedding[0], np.ndarray)

    exec = MyExecutor()
    bd = EncodeDriver()

    bd.attach(exec, runtime=None)
    docs = list(random_docs(10))

    ds = DocumentArray(docs)

    bd._apply_all(ds)
    encode_mock.assert_called()


def test_extract_multi_fields_with_ndarray_type(mocker):
    encode_mock = mocker.Mock()

    class MyExecutor(BaseEncoder):
        def encode(self, id: 'np.ndarray', embedding: 'np.ndarray'):
            encode_mock()
            assert isinstance(id, np.ndarray)
            assert isinstance(embedding, np.ndarray)
            assert isinstance(id[0], str)
            assert isinstance(embedding[0], np.ndarray)

    exec = MyExecutor()
    bd = EncodeDriver()

    bd.attach(exec, runtime=None)
    docs = list(random_docs(10))

    ds = DocumentArray(docs)

    bd._apply_all(ds)
    encode_mock.assert_called()


def test_extract_bad_fields(mocker):
    encode_mock = mocker.Mock()

    class MyExecutor(BaseEncoder):
        def encode(self, data):
            encode_mock()

    exec = MyExecutor()
    bd = EncodeDriver()

    bd.attach(exec, runtime=None)
    docs = list(random_docs(10))

    ds = DocumentArray(docs)

    with pytest.raises(
        AttributeError, match='is now deprecated and not a valid argument'
    ):
        bd._apply_all(ds)
    encode_mock.assert_not_called()

    class MyExecutor(BaseEncoder):
        def encode(self, hello):
            encode_mock()

    exec = MyExecutor()
    bd = EncodeDriver()
    bd.attach(exec, runtime=None)

    with pytest.raises(AttributeError, match='are invalid Document attributes'):
        bd._apply_all(ds)
    encode_mock.assert_not_called()

    class MyExecutor(BaseEncoder):
        def encode(self, mimeType):
            encode_mock()

    exec = MyExecutor()
    bd = EncodeDriver()
    bd.attach(exec, runtime=None)

    with pytest.raises(AttributeError, match='you give them in CamelCase'):
        bd._apply_all(ds)
    encode_mock.assert_not_called()


def test_extract_bad_fields_no_strict_args(mocker):
    encode_mock = mocker.Mock()

    class MyExecutor(BaseEncoder):
        def encode(self, hello):
            encode_mock()

    exec = MyExecutor()
    bd = EncodeDriver(strict_method_args=False)

    bd.attach(exec, runtime=None)
    docs = list(random_docs(10))

    ds = DocumentArray(docs)

    bd._apply_all(ds)
    encode_mock.assert_not_called()


def test_exec_fn_arbitrary_name(mocker):
    encode_mock = mocker.Mock()

    class MyExecutor(BaseEncoder):
        def foo(self, id):
            assert isinstance(id[0], str)
            assert isinstance(id, list)
            encode_mock()

    exec = MyExecutor()
    bd = EncodeDriver(method='foo')

    bd.attach(exec, runtime=None)
    docs = list(random_docs(10))

    ds = DocumentArray(docs)

    bd._apply_all(ds)
    encode_mock.assert_called()


def test_exec_fn_return_dict(mocker):
    encode_mock = mocker.Mock()

    class MyExecutor(BaseEncoder):
        def encode(self, id):
            encode_mock()
            return [{'id': 'hello'}] * len(id)

    exec = MyExecutor()
    bd = EncodeDriver()

    bd.attach(exec, runtime=None)
    docs = list(random_docs(10))

    ds = DocumentArray(docs)

    bd._apply_all(ds)
    encode_mock.assert_called()

    for d in ds:
        assert d.id == 'hello'


def test_exec_fn_return_doc(mocker):
    encode_mock = mocker.Mock()

    class MyExecutor(BaseEncoder):
        def encode(self, id):
            encode_mock()
            return [Document(mime_type='image/png')] * len(id)

    exec = MyExecutor()
    bd = EncodeDriver()

    bd.attach(exec, runtime=None)
    docs = list(random_docs(10))

    ds = DocumentArray(docs)

    bd._apply_all(ds)
    encode_mock.assert_called()

    for d in ds:
        assert d.mime_type == 'image/png'


def test_exec_fn_annotation():
    class MyExecutor(BaseEncoder):
        def foo(
            self, a: 'np.ndarray', b: np.ndarray, c: np.float, *args, **kwargs
        ) -> 'np.ndarray':
            pass

    exec = MyExecutor()
    bd = EncodeDriver(method='foo', strict_method_args=False)

    bd.attach(exec, runtime=None)

    assert bd._exec_fn_return_is_ndarray
    assert bd._exec_fn_required_keys_is_ndarray == [True, True, False]
