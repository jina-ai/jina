from jina.flow import Flow
from tests import random_docs


def test_ws_streaming(mocker):
    m = mocker.Mock()

    def callback(x):
        m()
        print(x)

    f = Flow(rest_api=True).add().add()

    with f:
        f.index(random_docs(10))
        f.search(random_docs(2), on_done=callback)
        m.assert_called_once()
