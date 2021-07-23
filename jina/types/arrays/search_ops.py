import re
from typing import Union, Dict

import numpy as np

if False:
    from .document import DocumentArray


class DocumentArraySearchOpsMixin:
    """ A mixin that provides search functionality to DocumentArrays"""

    operators = ['<', '>', '==', '!=', '<=', '>=', 'any', 'all']

    def find(
        self,
        regexes: Dict,
        traversal_paths: list = ['r'],
        operator: str = 'all',
        value: int = 1,
    ) -> None:
        """
        Find Documents that match the regular expressions in `regexes`.


        :param regexes: Dictionary of the form {tag:regex}
        :param traversal_paths: List specifying traversal paths
        :param operator: Operator used to accept/reject a document
        :param value: Number of regex that should match the operator to accept a Document.
                      This is ignored with operators `any` and `all`.
        :return: DocumentArray with Documents that match the regexes
        """

        assert (
            operator in self.operators
        ), f'operator={operator} is not a valid operator from {self.operators}'
        iterdocs = self.traverse_flat(traversal_paths)
        matched_counts = np.zeros(len(self), dtype=np.int32)
        filtered = DocumentArray()

        for tag_name, regex in regexes.items():
            regexes[tag_name] = re.compile(regex)

        for pos, doc in enumerate(iterdocs):
            for tag_name, pattern in regexes.items():
                if pattern.match(doc.tags[tag_name]):
                    matched_counts[pos] += 1

        if operator == '<':
            coordinate_flags = matched_counts < value
        elif operator == '>':
            coordinate_flags = matched_counts > value
        elif operator == '==':
            coordinate_flags = matched_counts == value
        elif operator == '!=':
            coordinate_flags = matched_counts != value
        elif operator == '<=':
            coordinate_flags = matched_counts <= value
        elif operator == '>=':
            coordinate_flags = matched_counts >= value
        elif operator == 'any':
            coordinate_flags = matched_counts >= 1
        elif operator == 'all':
            coordinate_flags = matched_counts == len(regexes)

        indices = np.where(coordinate_flags)[0].tolist()
        filtered.append(self[pos])

        return filtered
