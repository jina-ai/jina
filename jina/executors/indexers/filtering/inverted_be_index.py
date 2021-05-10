from typing import Dict

from collections import defaultdict
from functools import reduce


class BooleanExpression:
    def __init__(self, lookups: Dict, *args, **kwargs):
        self.expression = lookups

    @property
    def k(self):
        return len(self.expression.keys())

    def _break_expression(self):
        return [
            BooleanExpression(lookups={key: value})
            for key, value in self.expression.items()
        ]

    @property
    def conjunctions(self):
        return self._break_expression()

    def __str__(self):
        return ''.join(f'{key}:{value}-' for key, value in self.expression.items())

    def __eq__(self, other):
        return hash(str(self)) == hash(str(other))

    def __hash__(self):
        return hash(str(self))

    def __iter__(self):
        for be in self.conjunctions:
            yield be


class BooleanExpressionInvertedIndex:
    def __init__(self, *args, **kwargs):
        self.ids = {}  # map from BE id to expression or identifier to a vector index
        self.inverted_indexes = defaultdict(
            lambda: defaultdict(list)
        )  # defaultdict of inverted indexes (one per K) one per K, f

    def add(self, lookups: Dict):
        boolean_expression = BooleanExpression(lookups=lookups)
        if boolean_expression not in self.ids:
            self.ids[
                boolean_expression
            ] = True  # need to point somewhere to link to a vector Index

        inverted_index = self.inverted_indexes[boolean_expression.k]

        for conjunction in boolean_expression:
            assert conjunction.k == 1
            inverted_index[conjunction].append(boolean_expression)

    def query(self, lookups: Dict):
        boolean_expression = BooleanExpression(lookups=lookups)
        inverted_index_to_check = self.inverted_indexes[boolean_expression.k]

        candidates = {}
        for conjunction in boolean_expression:
            candidates[conjunction] = inverted_index_to_check[conjunction]

        # find the intersection between `lists` in different `candidates`

        return list(
            reduce(set.intersection, [set(item) for item in candidates.values()])
        )
