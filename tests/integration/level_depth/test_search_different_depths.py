import os
from jina.flow import Flow
from tests import JinaTestCase

cur_dir = os.path.dirname(os.path.abspath(__file__))


class SearchDifferentLevelDepthTestCase(JinaTestCase):

    def setUp(self) -> None:
        super().setUp()
        os.environ['CUR_DIR_LEVEL_DEPTH'] = cur_dir

    def tearDown(self) -> None:
        super().tearDown()
        del os.environ['CUR_DIR_LEVEL_DEPTH']

    def test_index_depth_0_search_depth_1(self):
        index_data = [
            'I am chunk 0 of doc 1, I am chunk 1 of doc 1, I am chunk 2 of doc 1',
            'I am chunk 0 of doc 2, I am chunk 1 of doc 2',
            'I am chunk 0 of doc 3, I am chunk 1 of doc 3, I am chunk 2 of doc 3, I am chunk 3 of doc 3',
        ]

        index_flow = Flow().load_config(os.path.join(cur_dir, 'flow-index.yml'))
        with index_flow:
            index_flow.index(index_data)

        def validate_level_depth_1(resp):
            print(f'JOAN RESP: \n {resp}')
            self.assertEqual(len(resp.docs), 3)
            for doc in resp.docs:
                self.assertEqual(doc.level_depth, 1)
                self.assertEqual(len(doc.matches), 1)
                self.assertEqual(doc.matches[0].id, doc.id)  # done on purpose

        search_data = [
            'I am chunk 1 of doc 1,',
            'I am chunk 0 of doc 2,',
            'I am chunk 3 of doc 3',
        ]

        print(f'********************** SEARCH ***********************************')

        search_flow = Flow().load_config(os.path.join(cur_dir, 'flow-query.yml'))
        with search_flow:
            search_flow.search(input_fn=search_data,  output_fn=validate_level_depth_1, callback_on_body=True, level_depth=1)

        self.add_tmpfile(os.path.join(os.getenv('TEST_WORKDIR'), 'test_workspace'))
