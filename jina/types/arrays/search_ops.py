import re
import random
import operator
from typing import Dict, Optional, Union, Tuple

if False:
    from .document import DocumentArray


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
        regexes: Dict[str, Union[str, re.Pattern]],
        traversal_paths: Tuple[str] = ('r',),
        operator: str = '>=',
        threshold: Optional[int] = None,
    ) -> 'DocumentArray':
        """
        Find Documents whose tag match the regular expressions in `regexes`.
        If `regexes` contain several regular expressions an `operator` can be used to
        specify a decision depending on the of regular expression matches specified by `value`.

        The supported operators are: ['<', '>', '==', '!=', '<=', '>=']

        Example: If `len(regexes)=3` then the documents from the DocumentArray will be accepted if
                 they match all 3 regular expressions.

        Example: If `len(regexes)=3`,  `value=2` and `operator='>='` then the documents
                 from the DocumentArray will be accepted if they match at least 2 regular expressions.

        :param regexes: Dictionary of the form {tag: Optional[str, regex]}
        :param traversal_paths: List specifying traversal paths
        :param operator: Operator used to accept/reject a document
        :param threshold: Number of regex that should match the operator to accept a Document.
                          If no value is provided `threshold=len(regexes)`.
        :return: DocumentArray with Documents that match the regexes
        """
        from .document import DocumentArray

        assert (
            operator in self.operators
        ), f'operator={operator} is not a valid operator from {self.operators.keys()}'

        operator_func = self.operators[operator]
        iterdocs = self.traverse_flat(traversal_paths)
        filtered = DocumentArray()

        threshold = threshold or len(regexes)

        for tag_name, regex in regexes.items():
            if isinstance(regex, str):
                regexes[tag_name] = re.compile(regex)

        for pos, doc in enumerate(iterdocs):
            counter = 0
            for tag_name, pattern in regexes.items():
                tag_value = doc.tags.get(tag_name, None)
                if tag_value:
                    if pattern.match(tag_value):
                        counter += 1
            if operator_func(counter, threshold):
                filtered.append(self[pos])

        return filtered

    def sample(self, k: int, seed: Optional[int] = None) -> 'DocumentArray':
        """random sample k elements from :class:`DocumentArray` without replacement.

        :param k: Number of elements to sample from the document array.
        :param seed: initialize the random number generator, by default is None. If set will
            save the state of the random function to produce certain outputs.
        :return: A sampled list of :class:`Document` represented as :class:`DocumentArray`.
        """
        from .document import DocumentArray

        if k > len(self):
            raise ValueError(
                f'Sample size {k} is greater than the length of Document {len(self)}'
            )
        if seed is not None:
            random.seed(seed)
        # NOTE, this could simplified to random.sample(self, k)
        # without getting indices and itemgetter etc.
        # however it's only work on DocumentArray, not DocumentArrayMemmap.
        indices = random.sample(range(len(self)), k)
        sampled = operator.itemgetter(*indices)(self)
        return DocumentArray(sampled)

    def shuffle(self, seed: Optional[int] = None) -> 'DocumentArray':
        """Randomly shuffle documents within the :class:`DocumentArray`.

        :param seed: initialize the random number generator, by default is None. If set will
            save the state of the random function to produce certain outputs.
        :return: The shuffled list of :class:`Document` represented as :class:`DocumentArray`.
        """
        from .document import DocumentArray

        return DocumentArray(self.sample(len(self), seed=seed))
