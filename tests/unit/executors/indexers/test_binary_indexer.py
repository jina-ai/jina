import copy
import os

import numpy as np
import pytest

from jina.executors.indexers import BaseIndexer
from jina.executors.indexers.keyvalue import BinaryPbIndexer
from jina.flow import Flow
from tests import random_docs, validate_callback


@pytest.mark.parametrize('random_workspace_name', ['JINA_TEST_WORKSPACE_BINARY_PB'])
def test_binarypb_in_flow(test_metas, mocker):
    docs = list(random_docs(10))

    def validate(req):
        assert len(docs) == len(req.docs)
        for d, d0 in zip(req.docs, docs):
            np.testing.assert_almost_equal(d.embedding,
                                           d0.embedding)

    f = Flow().add(uses='binarypb.yml')

    with f:
        f.index(docs)

    docs_no_embedding = copy.deepcopy(docs)
    for d in docs_no_embedding:
        d.ClearField('embedding')

    mock = mocker.Mock()
    with f:
        f.search(docs_no_embedding, on_done=mock)

    mock.assert_called_once()
    validate_callback(mock, validate)


def test_binarypb_update1(test_metas):
    with BinaryPbIndexer(metas=test_metas) as idxer:
        idxer.add(['1', '2', '3'], [b'oldvalue', b'same', b'random'])
        idxer.save()
        assert idxer.size == 3
        first_size = os.fstat(idxer.write_handler.body.fileno()).st_size
        save_abspath = idxer.save_abspath

    with BaseIndexer.load(save_abspath) as idxer:
        assert idxer.query('1') == b'oldvalue'

    with BaseIndexer.load(save_abspath) as idxer:
        assert idxer.query('1') == b'oldvalue'
        second_size = os.fstat(idxer.query_handler._body.fileno()).st_size
        assert second_size == first_size

    with BaseIndexer.load(save_abspath) as idxer:
        # some new value
        idxer.update(['1', '2'], [b'newvalue', b'same'])
        idxer.save()
        third_size = os.fstat(idxer.write_handler.body.fileno()).st_size
        assert third_size > first_size
        assert idxer.size == 3

    with BaseIndexer.load(save_abspath) as idxer:
        assert idxer.query('1') == b'newvalue'
        assert idxer.query('2') == b'same'
        assert idxer.query('3') == b'random'
        assert idxer.query('99') is None

    with BaseIndexer.load(save_abspath) as idxer:
        # partial update when missing keys encountered
        idxer.update(['1', '2', '99'], [b'newvalue2', b'newvalue3', b'decoy'])
        idxer.save()
        assert idxer.size == 3

    with BaseIndexer.load(save_abspath) as idxer:
        assert idxer.query('1') == b'newvalue2'
        assert idxer.query('2') == b'newvalue3'
        assert idxer.query('3') == b'random'
        assert idxer.query('99') is None


def test_binarypb_add_and_update_not_working(test_metas):
    with BinaryPbIndexer(metas=test_metas) as idxer:
        idxer.add(['11', '12'], [b'eleven', b'twelve'])
        idxer.save()
        # FIXME `add` and `update` won't work in the same context
        # since `.save` calls `.flush` on a closed handler
        # and the handler needs to have been
        # closed for us to allow querying in the `.update`
        with pytest.raises(AttributeError):
            idxer.update(['12'], [b'twelve-new'])
            idxer.save()
        assert idxer.size == 2
        save_abspath = idxer.save_abspath

    with BaseIndexer.load(save_abspath) as idxer:
        idxer.update(['12'], [b'twelve-new'])
        idxer.save()

    with BaseIndexer.load(save_abspath) as idxer:
        assert idxer.query('11') == b'eleven'
        assert idxer.query('12') == b'twelve-new'
        assert idxer.size == 2


def test_binarypb_delete(test_metas):
    with BinaryPbIndexer(metas=test_metas) as idxer:
        idxer.add(['1', '2', '3'], [b'oldvalue', b'same', b'random'])
        idxer.save()
        assert idxer.size == 3
        save_abspath = idxer.save_abspath

    with BaseIndexer.load(save_abspath) as idxer:
        assert idxer.query('1') == b'oldvalue'

    with BaseIndexer.load(save_abspath) as idxer:
        idxer.delete(iter(['1', '2']))
        idxer.save()
        assert idxer.size == 1

    with BaseIndexer.load(save_abspath) as idxer:
        assert idxer.query('1') is None
        assert idxer.query('2') is None
        assert idxer.query('3') == b'random'


def test_binarypb_update_twice(test_metas):
    """two updates in a row does work"""
    with BinaryPbIndexer(metas=test_metas) as idxer:
        idxer.add(['1', '2', '3'], [b'oldvalue', b'same', b'random'])
        idxer.save()
        assert idxer.size == 3
        save_abspath = idxer.save_abspath

    with BaseIndexer.load(save_abspath) as idxer:
        idxer.update(['1'], [b'newvalue'])
        idxer.update(['2'], [b'othernewvalue'])
        idxer.save()

    with BaseIndexer.load(save_abspath) as idxer:
        assert idxer.query('1') == b'newvalue'
        assert idxer.query('2') == b'othernewvalue'
