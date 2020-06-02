import unittest
from tests import JinaTestCase
from jina.main.parser import set_client_cli_parser
from jina.helper import get_parsed_args


class MyTestCase(JinaTestCase):
    def test_get_parsed_args_parse_list(self):
        kwargs = {'filter-by': ['a', 'b']}
        parser = set_client_cli_parser()
        args, p_args, un_args = get_parsed_args(kwargs, parser)
        self.assertEqual(len(args), 3)
        self.assertEqual(len(p_args.filter_by), 2)
        self.assertEqual(len(un_args), 0)


if __name__ == '__main__':
    unittest.main()
