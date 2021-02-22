import os

from jina import Segmenter, Crafter


class SimpleCrafter(Crafter):

    def craft(self, tags):
        return {'text': tags['caption'],
                'uri': f'{os.environ["HW_WORKDIR"]}/people-img/{tags["image"]}'}


class BiSegmenter(Segmenter):

    def segment(self, text, uri):
        return [
            {'text': text, 'mime_type': 'text/plain'},
            {'uri': uri, 'mime_type': 'image/jpeg'}
        ]
