import os

from jina import Executor, DocumentArray, requests, Document


class Segmenter(Executor):
    @requests(on='/index')
    def segment(self, docs: DocumentArray):
        """
        Read the data and add tags.

        :param docs: received documents.
        :return: crafted data
        """
        items = []
        for doc in docs:
            text = doc.tags['caption']
            uri = f'{os.environ["HW_WORKDIR"]}/people-img/{doc.tags["image"]}'
            item = [
                {'text': text, 'mime_type': 'text/plain'},
                {'uri': uri, 'mime_type': 'image/jpeg'},
            ]
            items.append(item)
        return items
