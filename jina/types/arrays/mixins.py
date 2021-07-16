import re
import operator
from typing import List, Dict, Iterable

from jina import DocumentArray


class FilterMixin:
    def fuzzy_filter(
        self, regexes: List[Dict[str]], traversal_paths: Iterable[str] = ['r']
    ):
        """Filter document array by tags attribute."""
        filtered = DocumentArray()
        docs = self.traverse_flat(traversal_paths)
        for tag_name, regex in regexes:
            pattern = re.compile(regex)
            for doc in docs:
                if re.match(pattern, doc.get(tag_name, '')):
                    filtered.append(doc)
        return filtered

    def hard_filter(
        self,
        conditions: List[tuple(str, str, str)],
        traversal_paths: Iterable[str] = ['r'],
    ):
        """Filter documents by hard match on tags."""
        filtered = DocumentArray()
        docs = self.traverse_flat(traversal_paths)
        operators_map = {
            'gt': operator.gt,
            'lt': operator.lt,
            'eq': operator.eq,
            'ne': operator.ne,
            'ge': operator.ge,
            'ne': operator.ne,
        }
        for condition in conditions:
            operator_instance = operators_map.get(condition[1], None)
            if operator_instance:
                for doc in docs:
                    tag_name = doc.get(condition[0], None)
                    tag_value = doc.get(condition[2], None)
                    if tag_name and tag_value:
                        if operator_instance(tag_name, tag_value):
                            filtered.append(doc)
        return filtered
