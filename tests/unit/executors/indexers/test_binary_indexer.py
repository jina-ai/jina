import copy
import os
import time

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
            np.testing.assert_almost_equal(d.embedding, d0.embedding)

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


@pytest.mark.parametrize('delete_on_dump', [True, False])
def test_binarypb_update1(test_metas, delete_on_dump):
    with BinaryPbIndexer(metas=test_metas, delete_on_dump=delete_on_dump) as idxer:
        idxer.add(['1', '2', '3'], [b'oldvalue', b'same', b'random'])
        idxer.save()
        assert idxer.size == 3

    first_size = os.path.getsize(idxer.index_abspath)
    save_abspath = idxer.save_abspath

    with BaseIndexer.load(save_abspath) as idxer:
        assert idxer.query(['1']) == [b'oldvalue']

    with BaseIndexer.load(save_abspath) as idxer:
        assert idxer.query(['1']) == [b'oldvalue']

    second_size = os.path.getsize(idxer.index_abspath)
    assert second_size == first_size

    with BaseIndexer.load(save_abspath) as idxer:
        # some new value
        idxer.update(['1', '2'], [b'newvalue', b'same'])
        idxer.save()

    third_size = os.path.getsize(idxer.index_abspath)
    if delete_on_dump:
        assert third_size == first_size
    else:
        assert third_size > first_size
    assert idxer.size == 3

    with BaseIndexer.load(save_abspath) as idxer:
        assert idxer.query(['1']) == [b'newvalue']
        assert idxer.query(['2']) == [b'same']
        assert idxer.query(['3']) == [b'random']
        assert idxer.query(['99']) == [None]

    with BaseIndexer.load(save_abspath) as idxer:
        # partial update when missing keys encountered
        idxer.update(['1', '2', '99'], [b'abcvalue', b'abcd', b'WILL_BE_IGNORED'])
        idxer.save()
        assert idxer.size == 3

    fourth_size = os.path.getsize(idxer.index_abspath)
    if delete_on_dump:
        assert fourth_size == first_size
    else:
        assert fourth_size > first_size
    assert idxer.size == 3

    with BaseIndexer.load(save_abspath) as idxer:
        assert idxer.query(['1']) == [b'abcvalue']
        assert idxer.query(['2']) == [b'abcd']
        assert idxer.query(['3']) == [b'random']
        assert idxer.query(['99']) == [None]
        assert idxer.query(['1', '2']) == [b'abcvalue', b'abcd']
        assert idxer.query(['1', '2', '3']) == [b'abcvalue', b'abcd', b'random']


@pytest.mark.parametrize('delete_on_dump', [True, False])
def test_binarypb_add_and_update_not_working(test_metas, delete_on_dump):
    with BinaryPbIndexer(metas=test_metas, delete_on_dump=delete_on_dump) as idxer:
        idxer.add(['11', '12', '13'], [b'eleven', b'twelve', b'thirteen'])
        idxer.save()
        # FIXME `add` and `update` won't work in the same context
        # since `.save` calls `.flush` on a closed handler
        # and the handler needs to have been
        # closed for us to allow querying in the `.update`
        with pytest.raises(AttributeError):
            idxer.update(['12'], [b'twelve-new'])
            idxer.save()
        assert idxer.size == 3
        save_abspath = idxer.save_abspath

    with BaseIndexer.load(save_abspath) as idxer:
        idxer.update(['12'], [b'twelve-new'])
        idxer.save()

    with BaseIndexer.load(save_abspath) as idxer:
        assert idxer.query(['11']) == [b'eleven']
        assert idxer.query(['12']) == [b'twelve-new']
        assert idxer.query(['12', '13']) == [b'twelve-new', b'thirteen']
        assert idxer.size == 3
        assert idxer.sample() in (b'eleven', b'twelve-new', b'thirteen')


@pytest.mark.parametrize('delete_on_dump', [True, False])
def test_binarypb_delete(test_metas, delete_on_dump):
    with BinaryPbIndexer(metas=test_metas, delete_on_dump=delete_on_dump) as idxer:
        idxer.add(['1', '2', '3'], [b'oldvalue', b'same', b'random'])
        idxer.save()
        assert idxer.size == 3
        save_abspath = idxer.save_abspath

    with BaseIndexer.load(save_abspath) as idxer:
        assert idxer.size == 3
        assert idxer.query('1') == [b'oldvalue']

    with BaseIndexer.load(save_abspath) as idxer:
        idxer.delete(iter(['1', '2']))
        idxer.save()
        assert idxer.size == 1

    with BaseIndexer.load(save_abspath) as idxer:
        assert idxer.query('1') == [None]
        assert idxer.query('2') == [None]
        assert idxer.query('3') == [b'random']


@pytest.mark.parametrize('delete_on_dump', [True, False])
def test_binarypb_update_twice(test_metas, delete_on_dump):
    """two updates in a row does work"""
    with BinaryPbIndexer(metas=test_metas, delete_on_dump=delete_on_dump) as idxer:
        idxer.add(['1', '2', '3'], [b'oldvalue', b'same', b'random'])
        idxer.save()
        assert idxer.size == 3
        save_abspath = idxer.save_abspath

    with BaseIndexer.load(save_abspath) as idxer:
        idxer.update(['1', '2'], [b'newvalue', b'othernewvalue'])
        idxer.save()

    with BaseIndexer.load(save_abspath) as idxer:
        assert idxer.query(['1']) == [b'newvalue']
        assert idxer.query(['2']) == [b'othernewvalue']
        assert idxer.query(['1', '2']) == [b'newvalue', b'othernewvalue']


# benchmark only
@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ, reason='skip the benchmark test on github workflow'
)
@pytest.mark.parametrize('delete_on_dump', [True, False])
def test_binarypb_benchmark(test_metas, delete_on_dump):
    entries = 100000
    nr_to_update = 10000
    keys = np.arange(entries)
    values = np.random.randint(0, 10, size=entries).astype(bytes)

    with BinaryPbIndexer(metas=test_metas, delete_on_dump=delete_on_dump) as idxer:
        idxer.add(keys, values)
        idxer.save()
        assert idxer.size == entries
        save_abspath = idxer.save_abspath

    new_values = np.random.randint(0, 10, size=nr_to_update).astype(bytes)

    with BaseIndexer.load(save_abspath) as idxer:
        idxer.update(keys[:nr_to_update], new_values)
        time_now = time.time()
        idxer.save()

    time_end = time.time()
    print(
        f'delete_on_dump = {delete_on_dump}, entries={entries}. took {time_end - time_now} seconds'
    )


def test_kvindexer_iterate(test_metas):
    """two updates in a row does work"""
    with BinaryPbIndexer(metas=test_metas) as idxer:
        idxer.add(['1', '2', '3'], [b'oldvalue', b'same', b'random'])
        save_abspath = idxer.save_abspath

    with BaseIndexer.load(save_abspath) as idxer:
        assert list(idxer) == [[b'oldvalue'], [b'same'], [b'random']]
