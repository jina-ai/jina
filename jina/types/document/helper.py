from typing import Iterable, Tuple, List

import numpy as np

from . import Document


def extract_docs(docs: Iterable['Document'], embedding: bool) -> Tuple['np.ndarray',
                                                                       List['Document'], List[Tuple[str, str]]]:
    """Iterate over a list of protobuf documents and extract chunk-level information from them

    :param docs: an iterable of protobuf documents
    :param embedding: an indicator of extracting embedding or not.
                    If ``True`` then all doc-level embedding are extracted.
                    If ``False`` then ``text``, ``buffer``, ``blob`` info of each doc are extracted
    :return: A tuple of 3 pieces:

            - a numpy ndarray of extracted info
            - the corresponding doc references
            - the doc_id list where the doc has no contents, useful for debugging
    """
    contents = []
    docs_pts = []
    bad_doc_ids = []

    if embedding:
        _attr = 'embedding'
    else:
        _attr = 'content'

    for doc in docs:
        content = getattr(doc, _attr)

        if content is not None:
            contents.append(content)
            docs_pts.append(doc)
        else:
            bad_doc_ids.append((doc.id, doc.parent_id))

    contents = np.stack(contents) if contents else None
    return contents, docs_pts, bad_doc_ids


class DocGroundtruthPair:
    """
    Helper class to expose common interface to the traversal logic of the BaseExecutable Driver.
    It is important to note that it checks the matching structure of `docs` and `groundtruths`. It is important while
    traversing to ensure that then the driver can be applied at a comparable level of granularity and adjacency.
    This does not imply that you can't compare at the end a document with 10 matches with a groundtruth with 20 matches
    """

    def __init__(self, doc: 'Document', groundtruth: 'Document'):
        self.doc = doc
        self.groundtruth = groundtruth

    @property
    def matches(self) -> Iterable['DocGroundtruthPair']:
        for doc, groundtruth in zip(self.doc.matches, self.groundtruth.matches):
            yield DocGroundtruthPair(doc, groundtruth)

    @property
    def chunks(self) -> Iterable['DocGroundtruthPair']:
        for doc, groundtruth in zip(self.doc.chunks, self.groundtruth.chunks):
            yield DocGroundtruthPair(doc, groundtruth)
