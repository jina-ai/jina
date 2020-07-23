import unittest

from jina.main.parser import set_pea_parser
from jina.peapods.splitter_pea import SplitterPea
from jina.drivers.control import SplitRouteDriver
from tests import JinaTestCase


class SplitterPeaTestCase(JinaTestCase):

    def test_splitter_pea(self):
        args = set_pea_parser()
        pea = SplitterPea(args)
        pea.load_executor()
        self.assertEqual(pea.executor.name, 'split_route')
        self.assertIsInstance(pea.executor._drivers['IndexRequest'][0], SplitRouteDriver)
        self.assertIsInstance(pea.executor._drivers['SearchRequest'][0], SplitRouteDriver)
        self.assertIsInstance(pea.executor._drivers['TrainRequest'][0], SplitRouteDriver)
        self.assertIsInstance(pea.executor._drivers['ControlRequest'][0], SplitRouteDriver)

if __name__ == '__main__':
    unittest.main()
