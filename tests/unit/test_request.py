from jina.clients.python.request import _generate
from tests import JinaTestCase


class RequestTestCase(JinaTestCase):

    def test_request_generate(self):

        def random_lines(num_lines):
            for j in range(num_lines):
                yield "https://github.com 'i\'m dummy doc %d'" % j

        req = _generate(data=random_lines(100), batch_size=100)

        assert len(list(req)) == 1
