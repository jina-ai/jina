from typing import Dict, List

from collections import defaultdict
from functools import reduce


class BooleanExpression:
    """A Boolean expression class represents a boolean expression (following the syntax of `querylang).

    A Boolean Expression is formed by a set of `predicates` (which are themselves `BooleanExpressions`).

    # TODO: Point to the QueryLanguage specifications
    """

    def __init__(self, lookups: Dict, *args, **kwargs):
        self.expression = lookups

    @property
    def k(self):
        """The number of predicates present in the `expression`. (Since the `BooleanExpressionInvertedIndex` does not support NOT operations)
        it does simply have a count on predicates. In the paper this count should be more complex when full complexity contained

        .. # noqa: DAR201
        """
        return len(self.expression.keys())

    def _break_expression(self):
        """
        Break expression into smaller expressions of a single predicate to be used as key to index in inverted index

        .. # noqa: DAR201
        """
        return [
            BooleanExpression(lookups={key: value})
            for key, value in self.expression.items()
        ]

    @property
    def predicates(self):
        """
        The list of predicates present in the `expression`.

        .. # noqa: DAR201
        """
        return self._break_expression()

    def __str__(self):
        num_expessions = self.k
        return ''.join(
            f'{key}:{value}-' if idx < num_expessions - 1 else f'{key}:{value}'
            for idx, (key, value) in enumerate(self.expression.items())
        )

    def __eq__(self, other):
        return hash(str(self)) == hash(str(other))

    def __gt__(self, other):
        return str(self) > str(other)

    def __hash__(self):
        return hash(str(self))

    def __iter__(self):
        for be in self.predicates:
            yield be


class BooleanExpressionInvertedIndex:
    """A simple and naive implementation of the CNF Algorithm (https://theory.stanford.edu/~sergei/papers/vldb09-indexing.pdf)

    .. note::
        Currently this inverted index assumes that all the `lookups` are conjunctions. And it does not support the NOT condition
    """

    def __init__(self, *args, **kwargs):
        self.ids = {}  # map from BE id to expression or identifier to a vector index
        self.inverted_indexes = defaultdict(
            lambda: defaultdict(list)
        )  # defaultdict of inverted indexes (one per K) one per K, f
        self.max_k = 0

    def add(self, lookups: Dict) -> None:
        """
        Add an expression (provided by the `lookup` dictionary) to the inverted index.

        :param lookups: A dictionary expressing the `boolean expression` to insert
        """
        boolean_expression = BooleanExpression(lookups=lookups)
        self.max_k = max(boolean_expression.k, self.max_k)
        if boolean_expression not in self.ids:
            self.ids[
                boolean_expression
            ] = True  # need to point somewhere to link to a vector Index

        inverted_index = self.inverted_indexes[boolean_expression.k]

        for conjunction in boolean_expression:
            assert conjunction.k == 1
            inverted_index[conjunction].append(boolean_expression)

    def query(self, lookups: Dict) -> List[BooleanExpression]:
        """
        Add an expression (provided by the `lookup` dictionary) to the inverted index.

        :param lookups: A dictionary expressing the `boolean expression` to query
        :return: the list of matched boolan expressions
        """
        boolean_expression = BooleanExpression(lookups=lookups)

        candidates = defaultdict(list)
        for k in reversed(range(1, self.max_k + 1)):
            inverted_index_to_check = self.inverted_indexes[k]

            for conjunction in boolean_expression:
                candidates[conjunction].extend(inverted_index_to_check[conjunction])

        # find the intersection between `lists` in different `candidates`
        return list(
            reduce(set.intersection, [set(item) for item in candidates.values()])
        )

    def _print(self):
        for k in reversed(range(self.max_k + 1)):
            k_str = f' k: {k} => \n '
            for key, values in self.inverted_indexes[k].items():
                values_str = ''.join(f'{str(value)}, ' for value in values)
                k_str += f'{key} => {values_str}\n'
            print(k_str)
