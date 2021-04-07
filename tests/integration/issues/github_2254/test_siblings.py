from jina import Flow, Document
from jina.executors.segmenters import BaseSegmenter
from jina.executors.decorators import single

from tests import validate_callback


class SimpleSegmenter(BaseSegmenter):
    def __init__(self, sep=','):
        super(SimpleSegmenter, self).__init__()
        self.sep = sep

    @single
    def segment(self, text, *args, **kwargs):
        return [{'text': t, 'mime_type': 'text/plain'} for t in text.split(self.sep)]


def test_segment_siblings(mocker):
    test_text = '1,2,3,4,5 a b c'

    def validate(resp):
        assert resp.index.docs[0].chunks[0].siblings == len(
            test_text.split(',') + test_text.split(' ')
        )

    f = Flow().load_config('flow.yml')

    mock = mocker.Mock()
    with f:
        f.index(
            [
                Document(text=test_text),
            ],
            on_done=mock,
        )
    mock.assert_called_once()
    validate_callback(mock, validate)
