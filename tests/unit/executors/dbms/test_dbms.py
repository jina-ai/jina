import os

from jina.drivers.index import DBMSIndexDriver
from jina.executors.indexers.dbms import BaseDBMSIndexer
from jina.executors.indexers.dbms.keyvalue import KeyValueDBMSIndexer
from tests import get_documents


def _get_ids_vecs_meta(docs):
    ids, vecs, metas = zip(
        *[
            (
                doc.id,
                doc.embedding,
                DBMSIndexDriver._doc_without_embedding(doc).SerializeToString(),
            )
            for doc in docs
        ]
    )
    return ids, vecs, metas


def test_dbms_keyvalue(tmpdir, test_metas):
    docs = list(get_documents(chunks=False, nr=10, same_content=True))
    ids, vecs, metas = _get_ids_vecs_meta(docs)

    save_path = None
    with KeyValueDBMSIndexer(index_filename='dbms', metas=test_metas) as indexer:
        indexer.add(ids, vecs, metas)
        assert indexer.size == len(docs)
        save_path = indexer.save_abspath
        indexer.dump(os.path.join(tmpdir, 'dump1'), 2)

        # we can index and dump again in the same context
        docs2 = list(
            get_documents(chunks=False, nr=10, same_content=True, index_start=len(docs))
        )
        ids, vecs, metas = _get_ids_vecs_meta(docs2)
        indexer.add(ids, vecs, metas)
        assert indexer.size == 2 * len(docs)
        indexer.dump(os.path.join(tmpdir, 'dump2'), 3)

    new_docs = list(get_documents(chunks=False, nr=10, same_content=False))
    ids, vecs, meta = zip(
        *[
            (
                doc.id,
                doc.embedding,
                DBMSIndexDriver._doc_without_embedding(doc).SerializeToString(),
            )
            for doc in new_docs
        ]
    )

    # assert contents update
    with BaseDBMSIndexer.load(save_path) as indexer:
        indexer.update(ids, vecs, meta)
        assert indexer.size == 2 * len(docs)

    # assert contents update
    with BaseDBMSIndexer.load(save_path) as indexer:
        indexer.delete([d.id for d in docs])
        assert indexer.size == len(docs)
