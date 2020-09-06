import os
import shutil

import pytest

from jina.flow import Flow

cur_dir = os.path.dirname(os.path.abspath(__file__))


def rm_files(file_paths):
    for file_path in file_paths:
        if os.path.exists(file_path):
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path, ignore_errors=False, onerror=None)

@pytest.mark.skip('based on discussion on Sept. 1, 2020, we will refactor it in another way')
def test_index_depth_0_search_depth_1():
    os.environ['CUR_DIR_GRANULARITY'] = cur_dir
    os.environ['TEST_WORKDIR'] = os.getcwd()
    index_data = [
        'I am chunk 0 of doc 1, I am chunk 1 of doc 1, I am chunk 2 of doc 1',
        'I am chunk 0 of doc 2, I am chunk 1 of doc 2',
        'I am chunk 0 of doc 3, I am chunk 1 of doc 3, I am chunk 2 of doc 3, I am chunk 3 of doc 3',
    ]

    index_flow = Flow().load_config('flow-index.yml')
    with index_flow:
        index_flow.index(index_data)

    def validate_granularity_1(resp):
        assert len(resp.docs) == 3
        for doc in resp.docs:
            assert doc.granularity == 1
            assert len(doc.matches) == 1
            assert doc.matches[0].id == doc.id  # done on purpose
            assert doc.matches[0].granularity == 0

        assert resp.docs[0].text == 'I am chunk 1 of doc 1,'
        assert resp.docs[0].matches[0].text == 'I am chunk 0 of doc 1, I am chunk 1 of doc 1, I am chunk 2 of doc 1'

        assert resp.docs[1].text == 'I am chunk 0 of doc 2,'
        assert resp.docs[1].matches[0].text == 'I am chunk 0 of doc 2, I am chunk 1 of doc 2'

        assert resp.docs[2].text == 'I am chunk 3 of doc 3'
        assert resp.docs[2].matches[
                   0].text == 'I am chunk 0 of doc 3, I am chunk 1 of doc 3, I am chunk 2 of doc 3, I am chunk 3 of doc 3'

    search_data = [
        'I am chunk 1 of doc 1,',
        'I am chunk 0 of doc 2,',
        'I am chunk 3 of doc 3',
    ]

    search_flow = Flow().load_config('flow-query.yml')
    with search_flow:
        search_flow.search(input_fn=search_data, output_fn=validate_granularity_1, callback_on_body=True, granularity=1)

    rm_files([os.path.join(os.getenv('TEST_WORKDIR'), 'test_workspace')])
    del os.environ['CUR_DIR_GRANULARITY']
    del os.environ['TEST_WORKDIR']
