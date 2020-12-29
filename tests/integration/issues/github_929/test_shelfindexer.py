import os
import shutil

import pytest

from jina.flow import Flow
from jina.logging.profile import used_memory
from jina.proto import jina_pb2
from tests import random_docs

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.parametrize('uses', ['binarypb.yml'])
def test_shelf_in_flow(uses, mocker):
    m1 = used_memory()
    # shelve does not support embed > 1000??
    # _dbm.error: cannot add item to database
    # HASH: Out of overflow pages.  Increase page size
    docs = random_docs(10000, embed_dim=1000)
    f = Flow(callback_on='body').add(uses=os.path.join(cur_dir, uses))

    with f:
        f.index(docs)

    m2 = used_memory()
    d = jina_pb2.DocumentProto()

    def validate(req):
        mock()
        m4 = used_memory()
        print(f'before: {m1}, after index: {m2}, after loading: {m3} after searching {m4}')

    mock = mocker.Mock()

    with f:
        m3 = used_memory()
        f.search([d], on_done=validate)

    shutil.rmtree('test-workspace', ignore_errors=False, onerror=None)
    mock.assert_called_once()
