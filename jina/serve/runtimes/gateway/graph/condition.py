from docarray import DocumentArray


class Condition:
    """
    :class Condition is a class that describes how a condition is applied to a DocumentArray

    :param condition_repr: A dictionary representation of a condition
    """

    def __init__(self, condition_repr):
        self._condition = condition_repr

    def filter(self, docs):
        """
        Applies the filter defined by condition

        :param docs: DocArray where to apply the filter
        :return: the resulting DocArray
        """
        return docs.find(self._condition)
