from jina.executors.indexers.vector import NumpyIndexer


def test_separated_workspace(test_metas):
    indexer = NumpyIndexer()
    # this values come from v0.8.12 before introducing JAML, add here for regression
    assert not indexer.separated_workspace
    assert indexer.pea_id == 0
    assert indexer.workspace == './'
    assert indexer.py_modules == None
    assert indexer.pea_workspace == './/None-0'
    assert indexer.name.startswith('jina.executors.indexers')