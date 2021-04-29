from .traversable import TraversableSequence
from ..arrays.doc_groundtruth import DocumentGroundtruthSequence
from ...helper import deprecated_class


@deprecated_class(
    new_class=DocumentGroundtruthSequence,
    custom_msg="The class has been moved to '..types.arrays', keeping its original name.",
)
class DocumentGroundtruthSequence(TraversableSequence):
    """
    :class:`DocumentGroundtruthSequence` is deprecated. It moved to `jina.types.array.doc_groundtruth`.
    """

    pass
