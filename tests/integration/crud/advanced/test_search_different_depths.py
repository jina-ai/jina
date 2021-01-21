import pytest

from jina import Document, DocumentSet
from jina.flow import Flow
from jina.types.document import UniqueId


def get_docs(contents):
    for i, content in enumerate(contents):
        d = Document()
        d.id = str(f'{i}' * 16)
        d.text = content
        yield d


# search for chunks in kw indexer
# search for chunks in vector indexer
# delete chunks in kw indexer
# delete chunks in vector indexer

# I can not  just insert the documents into the flow because they are chunked and the chunks have different ids.
    # let's look at the id generation of th chunk
    # but even then, it is not so easy. Do we get the chunks back when indexing?
# I could use the response from the index flow to see the chunks. However, I don't know which one is which.
# I mean, I could delete all the chunks and then index the doc again, but then we wouldn't use update


@pytest.mark.parametrize('restful', [False])
def test_index_depth_0_search_depth_1(tmpdir, mocker, monkeypatch, restful):
    monkeypatch.setenv("RESTFUL", restful)
    monkeypatch.setenv("JINA_TEST_LEVEL_DEPTH_WORKSPACE", str(tmpdir))

    index_data = get_docs([
        'chunk 0 of doc 1,chunk 1 of doc 1,chunk 2 of doc 1',
        'chunk 0 of doc 2,chunk 1 of doc 2',
        'chunk 0 of doc 3,chunk 1 of doc 3,chunk 2 of doc 3,chunk 3 of doc 3',
    ])



    response_docs = []
    def on_index_done(resp):
        response_docs.extend(resp.docs)
            # if doc.id == UniqueId(0):
            #     for chunk in doc.chunks:


    index_flow = Flow.load_config('flow-index.yml')
    with index_flow:
        index_flow.index(
            index_data,
            on_done=on_index_done
        )

    # only leave the chunks from the response docs which should be deleted
    # here we want to update the fist document. So we keep all chunks of the first document and remove the others
    for i in range(1,3):
        response_docs[i].chunks = []

    # now we run the flow again using a delete request which is ignored by the segmenter but will be handled by the
    # kv indexer and vector indexer
    delete_flow = Flow.load_config('flow-index.yml')
    with delete_flow:
        delete_flow.delete(response_docs)




    updated_data = [
        'updated chunk 0 of doc 1,chunk 1 of doc 1',
    ]

    # update_flow = Flow.load_config('flow-update.yml')
    # with update_flow:
    #     update_flow.update(updated_data)

    mock = mocker.Mock()
    def validate_granularity_1(resp):
        mock()
        assert len(resp.docs) == 3
        for doc in resp.docs:
            assert doc.granularity == 0
            assert len(doc.matches) == 3
            assert doc.matches[0].granularity == 0

        assert resp.docs[0].text == 'chunk 1 of doc 1,'
        assert (
                resp.docs[0].matches[0].text
                == 'chunk 0 of doc 1,chunk 1 of doc 1,chunk 2 of doc 1'
        )

        assert resp.docs[1].text == 'chunk 0 of doc 2,'
        assert (
                resp.docs[1].matches[0].text
                == 'chunk 0 of doc 2,chunk 1 of doc 2'
        )

        assert resp.docs[2].text == 'chunk 3 of doc 3'
        assert (
                resp.docs[2].matches[0].text
                == 'chunk 0 of doc 3,chunk 1 of doc 3,chunk 2 of doc 3,chunk 3 of doc 3'
        )

    search_data = [
        'chunk 1 of doc 1,',
        'chunk 0 of doc 2,',
        'chunk 3 of doc 3',
    ]

    with Flow.load_config('flow-query.yml') as search_flow:
        search_flow.search(
            input_fn=search_data,
            on_done=validate_granularity_1,
            callback_on='body',
        )

    mock.assert_called_once()
