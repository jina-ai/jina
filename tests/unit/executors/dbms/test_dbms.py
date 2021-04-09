from jina.drivers.dbms import _doc_without_embedding
from jina.executors.indexers.dbms import BaseDBMSIndexer
from jina.executors.indexers.dbms.keyvalue import KeyValueDBMSIndexer
from tests import get_documents


def test_dbms_keyvalue(tmpdir, test_metas):
    docs = list(get_documents(chunks=False, nr=10, same_content=True))
    ids, vecs, meta = zip(
        *[
            (doc.id, doc.embedding, _doc_without_embedding(doc).SerializeToString())
            for doc in docs
        ]
    )
    save_path = None
    with KeyValueDBMSIndexer(index_filename='dbms', metas=test_metas) as indexer:
        indexer.add(ids, vecs, meta)
        assert indexer.size == len(docs)
        save_path = indexer.save_abspath

    new_docs = list(get_documents(chunks=False, nr=10, same_content=False))
    ids, vecs, meta = zip(
        *[
            (doc.id, doc.embedding, _doc_without_embedding(doc).SerializeToString())
            for doc in new_docs
        ]
    )

    # assert contents update
    with BaseDBMSIndexer.load(save_path) as indexer:
        indexer.update(ids, vecs, meta)
        assert indexer.size == len(docs)

    # assert contents update
    with BaseDBMSIndexer.load(save_path) as indexer:
        indexer.delete([d.id for d in docs])
        assert indexer.size == 0
