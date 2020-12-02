import copy
import os

import numpy as np
import pytest

from jina.executors.indexers.keyvalue import BinaryPbIndexer
from jina.flow import Flow
from jina.types.ndarray.generic import NdArray
from tests import random_docs


@pytest.mark.parametrize('random_workspace_name', ['JINA_TEST_WORKSPACE_BINARY_PB'])
def test_binarypb_in_flow(test_metas):
    docs = list(random_docs(10))
    f = Flow(callback_on='body').add(uses='binarypb.yml')

    with f:
        f.index(docs, override_doc_id=False)

    def validate(req):
        assert len(docs) == len(req.docs)
        for d, d0 in zip(req.docs, docs):
            np.testing.assert_almost_equal(NdArray(d.embedding).value,
                                           NdArray(d0.embedding).value)

    docs_no_embedding = copy.deepcopy(docs)
    for d in docs_no_embedding:
        d.ClearField('embedding')
    with f:
        f.search(docs_no_embedding, output_fn=validate, override_doc_id=False)


def test_binarypb_update(tmpdir):
    # required for creating workspace
    metas = {
        'is_trained': False,
        'is_updated': False,
        'batch_size': None,
        'workspace': f'{tmpdir}',
        'name': None,
        'on_gpu': False,
        'warn_unnamed': False,
        'max_snapshot': 0,
        'py_modules': None,
        'pea_id': '{root.metas.pea_id}',
        'separated_workspace': '{root.metas.separated_workspace}',
    }
    with BinaryPbIndexer('pbidx', metas=metas) as idxer:
        idxer.add([1, 2, 3], [b'oldvalue', b'same', b'random'])
        idxer.save()
        assert idxer.size == 3
        assert idxer.query(1) == b'oldvalue'
        first_size = os.fstat(idxer.write_handler.body.fileno()).st_size

        # no update triggered AT ALL when encountering missing key
        # atomic op. at indexer level
        with pytest.raises(KeyError):
            idxer.update([1, 2, 99], [b'newvalue', b'same', b'decoy'])

        idxer.save()
        assert idxer.is_updated is False
        assert idxer.query(1) == b'oldvalue'
        second_size = os.fstat(idxer.write_handler.body.fileno()).st_size
        assert second_size == first_size

        # some new value
        idxer.update([1, 2], [b'newvalue', b'same'])
        # idxer.save()
        assert idxer.is_updated is True
        third_size = os.fstat(idxer.write_handler.body.fileno()).st_size
        assert third_size > first_size
        assert idxer.size == 3
        assert idxer.query(1) == b'newvalue'
        assert idxer.query(2) == b'same'
        assert idxer.query(3) == b'random'
        assert idxer.query(99) is None


def test_binarypb_delete(tmpdir):
    metas = {
        'is_trained': False,
        'is_updated': False,
        'batch_size': None,
        'workspace': f'{tmpdir}',
        'name': None,
        'on_gpu': False,
        'warn_unnamed': False,
        'max_snapshot': 0,
        'py_modules': None,
        'pea_id': '{root.metas.pea_id}',
        'separated_workspace': '{root.metas.separated_workspace}',
    }
    with BinaryPbIndexer('pbidx', metas=metas) as idxer:
        idxer.add([1, 2, 3], [b'oldvalue', b'same', b'random'])
        idxer.save()
        assert idxer.size == 3
        assert idxer.query(1) == b'oldvalue'
        idxer.delete(iter([1, 2]))
        idxer.save()
        assert idxer.size == 1
        assert idxer.query(1) == None
        assert idxer.query(2) == None
        assert idxer.query(3) == b'random'


