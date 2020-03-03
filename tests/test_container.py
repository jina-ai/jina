import time

from jina.main.parser import set_pea_parser
from jina.peapods.pea import ContainerizedPea
from tests import JinaTestCase


class MyTestCase(JinaTestCase):

    def test_simple_container(self):
        args = set_pea_parser().parse_args(['--image', 'jinaai/jina:latest-debian'])
        print(args)

        with ContainerizedPea(args) as cp:
            time.sleep(5)
