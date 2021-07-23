import re
import operator
from typing import Dict

import numpy as np


class DocumentArraySearchOpsMixin:
    """ A mixin that provides search functionality to DocumentArrays"""

    operators = {
        '<': operator.lt,
        '>': operator.gt,
        '==': operator.eq,
        '!=': operator.ne,
        '<=': operator.le,
        '>=': operator.ge,
    }

    def find(
        self,
        regexes: Dict,
        traversal_paths: list = ['r'],
        operator: str = '>=',
        value: int = 1,
    ) -> None:
        """
        Find Documents that match the regular expressions in `regexes`.
        If `regexes` contain several regular expressions an `operator` can be used to
        specify a decision depending on the of regular expression matches specified by `value`.

        The supported operators are: ['<', '>', '==', '!=', '<=', '>=']

        Example: If `len(regexes)=3`,  `value=2` and `operator='>='` then the documents
                 from the DocumentArray will be accepted if they match at least 2 regular expressions.

        :param regexes: Dictionary of the form {tag:regex}
        :param traversal_paths: List specifying traversal paths
        :param operator: Operator used to accept/reject a document
        :param value: Number of regex that should match the operator to accept a Document.
        :return: DocumentArray with Documents that match the regexes
        """
        from .document import DocumentArray

        assert (
            operator in self.operators
        ), f'operator={operator} is not a valid operator from {self.operators.keys()}'
        iterdocs = self.traverse_flat(traversal_paths)
        matched_counts = np.zeros(len(self), dtype=np.int32)
        filtered = DocumentArray()

        for tag_name, regex in regexes.items():
            regexes[tag_name] = re.compile(regex)

        for pos, doc in enumerate(iterdocs):
            for tag_name, pattern in regexes.items():
                tag_value = doc.tags.get(tag_name, None)
                if tag_value:
                    if pattern.match(tag_value):
                        matched_counts[pos] += 1

        operator_func = self.operators[operator]
        coordinate_flags = operator_func(matched_counts, value)
        indices = np.where(coordinate_flags)[0].tolist()

        for pos in indices:
            filtered.append(self[pos])

        return filtered
