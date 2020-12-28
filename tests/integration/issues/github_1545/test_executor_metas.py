from jina.executors.indexers.vector import NumpyIndexer


def test_separated_workspace(test_metas):
    indexer = NumpyIndexer()
    assert not indexer.separated_workspace
