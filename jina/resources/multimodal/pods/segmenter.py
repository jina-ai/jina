import os

from jina import Segmenter, Crafter
from jina.executors.decorators import single


class SimpleCrafter(Crafter):
    """Simple crafter for multimodal example."""

    @single
    def craft(self, tags):
        """
        Read the data and add tags.

        :param tags: tags of data
        :return: crafted data
        """
        return {
            'text': tags['caption'],
            'uri': f'{os.environ["HW_WORKDIR"]}/people-img/{tags["image"]}',
        }


class BiSegmenter(Segmenter):
    """Segmenter for multimodal example."""

    @single(slice_nargs=2)
    def segment(self, text, uri):
        """
        Segment data into text and uri.

        :param text: text data
        :param uri: uri data of images
        :return: Segmented data.
        """
        return [
            {'text': text, 'mime_type': 'text/plain'},
            {'uri': uri, 'mime_type': 'image/jpeg'},
        ]
