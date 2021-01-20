from jina.executors.indexers.vector import NumpyIndexer


def test_numpy_indexer_defaults(test_metas):
    indexer = NumpyIndexer()
    # this values come from v0.8.12 before introducing JAML, add here for regression
    assert indexer.pea_id == 0
    assert indexer.workspace == './'
    assert indexer.py_modules is None
    assert indexer.name.startswith('jina.executors.indexers')
