import pytest
import os

from jina import Flow, Executor, requests, DocumentArray


@pytest.fixture
def inject_secrets():
    os.environ['TEST_SECRET_KEY_1'] = 'test_secret_value_1'
    os.environ['TEST_SECRET_KEY_2'] = 'test_secret_value_2'
    yield
    os.unsetenv('TEST_SECRET_KEY_1')
    os.unsetenv('TEST_SECRET_KEY_2')


def test_secrets(inject_secrets):
    class SecretTestExecutor(Executor):

        def __init__(self, value_read_from_secret_1, value_read_from_secret_2, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.value_read_from_secret_1 = value_read_from_secret_1
            self.value_read_from_secret_2 = value_read_from_secret_2

        @requests
        def foo(self, docs, **kwargs):
            for doc in docs:
                doc.tags['TEST_SECRET_KEY_1'] = self.value_read_from_secret_1
                doc.tags['TEST_SECRET_KEY_2'] = self.value_read_from_secret_2

    f = Flow().add(uses=SecretTestExecutor, uses_with={'value_read_from_secret_1': '${{SECRETS.secret_1}}',
                                                       'value_read_from_secret_2': '${{SECRETS.secret_2}}'},
                   secrets=[{'name': 'secret_1', 'key': 'TEST_SECRET_KEY_1', 'type': 'env'}, {'name': 'secret_2', 'key': 'TEST_SECRET_KEY_2', 'type': 'env'}])

    with f:
        res = f.post(on='/', inputs=DocumentArray.empty(1))

    assert res[0].tags['TEST_SECRET_KEY_1'] == 'test_secret_value_1'
    assert res[0].tags['TEST_SECRET_KEY_2'] == 'test_secret_value_2'
