from jina.drivers.querylang.queryset.lookup import LookupLeaf
from tests import JinaTestCase


class LookupTestCase(JinaTestCase):

    class MockId:
        def __init__(self, identity):
            self.id = identity

    class MockStr:
        def __init__(self, string):
            self.str = string

    class MockIter:
        def __init__(self, iterable):
            self.iter = iterable

    def test_lookup_leaf_exact(self):
        leaf = LookupLeaf(id__exact=1)
        mock1 = LookupTestCase.MockId(1)
        self.assertTrue(leaf.evaluate(mock1))
        mock2 = LookupTestCase.MockId(2)
        self.assertFalse(leaf.evaluate(mock2))

    def test_lookup_leaf_neq(self):
        leaf = LookupLeaf(id__neq=1)
        mock1 = LookupTestCase.MockId(1)
        self.assertFalse(leaf.evaluate(mock1))
        mock2 = LookupTestCase.MockId(2)
        self.assertTrue(leaf.evaluate(mock2))

    def test_lookup_leaf_gt(self):
        leaf = LookupLeaf(id__gt=1)
        mock0 = LookupTestCase.MockId(0)
        self.assertFalse(leaf.evaluate(mock0))
        mock1 = LookupTestCase.MockId(1)
        self.assertFalse(leaf.evaluate(mock1))
        mock2 = LookupTestCase.MockId(2)
        self.assertTrue(leaf.evaluate(mock2))

    def test_lookup_leaf_gte(self):
        leaf = LookupLeaf(id__gte=1)
        mock0 = LookupTestCase.MockId(0)
        self.assertFalse(leaf.evaluate(mock0))
        mock1 = LookupTestCase.MockId(1)
        self.assertTrue(leaf.evaluate(mock1))
        mock2 = LookupTestCase.MockId(2)
        self.assertTrue(leaf.evaluate(mock2))

    def test_lookup_leaf_lt(self):
        leaf = LookupLeaf(id__lt=1)
        mock0 = LookupTestCase.MockId(0)
        self.assertTrue(leaf.evaluate(mock0))
        mock1 = LookupTestCase.MockId(1)
        self.assertFalse(leaf.evaluate(mock1))
        mock2 = LookupTestCase.MockId(2)
        self.assertFalse(leaf.evaluate(mock2))

    def test_lookup_leaf_lte(self):
        leaf = LookupLeaf(id__lte=1)
        mock0 = LookupTestCase.MockId(0)
        self.assertTrue(leaf.evaluate(mock0))
        mock1 = LookupTestCase.MockId(1)
        self.assertTrue(leaf.evaluate(mock1))
        mock2 = LookupTestCase.MockId(2)
        self.assertFalse(leaf.evaluate(mock2))

    def test_lookup_leaf_contains(self):
        leaf = LookupLeaf(str__contains='jina')
        mock0 = LookupTestCase.MockStr('hey jina how are you')
        self.assertTrue(leaf.evaluate(mock0))
        mock1 = LookupTestCase.MockStr('not here')
        self.assertFalse(leaf.evaluate(mock1))
        mock2 = LookupTestCase.MockStr('hey jInA how are you')
        self.assertFalse(leaf.evaluate(mock2))

    def test_lookup_leaf_icontains(self):
        leaf = LookupLeaf(str__icontains='jina')
        mock0 = LookupTestCase.MockStr('hey jInA how are you')
        self.assertTrue(leaf.evaluate(mock0))
        mock1 = LookupTestCase.MockStr('not here')
        self.assertFalse(leaf.evaluate(mock1))

    def test_lookup_leaf_startswith(self):
        leaf = LookupLeaf(str__startswith='jina')
        mock0 = LookupTestCase.MockStr('jina is the neural search solution')
        self.assertTrue(leaf.evaluate(mock0))
        mock1 = LookupTestCase.MockStr('hey, jina is the neural search solution')
        self.assertFalse(leaf.evaluate(mock1))
        mock2 = LookupTestCase.MockStr('JiNa is the neural search solution')
        self.assertFalse(leaf.evaluate(mock2))

    def test_lookup_leaf_istartswith(self):
        leaf = LookupLeaf(str__istartswith='jina')
        mock0 = LookupTestCase.MockStr('jina is the neural search solution')
        self.assertTrue(leaf.evaluate(mock0))
        mock1 = LookupTestCase.MockStr('hey, jina is the neural search solution')
        self.assertFalse(leaf.evaluate(mock1))
        mock2 = LookupTestCase.MockStr('JiNa is the neural search solution')
        self.assertTrue(leaf.evaluate(mock2))

    def test_lookup_leaf_endswith(self):
        leaf = LookupLeaf(str__endswith='jina')
        mock0 = LookupTestCase.MockStr('how is jina')
        self.assertTrue(leaf.evaluate(mock0))
        mock1 = LookupTestCase.MockStr('hey, jina is the neural search solution')
        self.assertFalse(leaf.evaluate(mock1))
        mock2 = LookupTestCase.MockStr('how is JiNa')
        self.assertFalse(leaf.evaluate(mock2))

    def test_lookup_leaf_iendswith(self):
        leaf = LookupLeaf(str__iendswith='jina')
        mock0 = LookupTestCase.MockStr('how is jina')
        self.assertTrue(leaf.evaluate(mock0))
        mock1 = LookupTestCase.MockStr('hey, jina is the neural search solution')
        self.assertFalse(leaf.evaluate(mock1))
        mock2 = LookupTestCase.MockStr('how is JiNa')
        self.assertTrue(leaf.evaluate(mock2))

    def test_lookup_leaf_regex(self):
        leaf = LookupLeaf(str__regex='j*na')
        mock0 = LookupTestCase.MockStr('hey, juna is good')
        self.assertTrue(leaf.evaluate(mock0))
        mock1 = LookupTestCase.MockStr('hey, Oinja is the neural search solution')
        self.assertFalse(leaf.evaluate(mock1))
        mock2 = LookupTestCase.MockStr('how is JiNa')
        self.assertFalse(leaf.evaluate(mock2))

    def test_lookup_leaf_in(self):
        leaf = LookupLeaf(id__in=[0, 1, 2, 3])
        mock0 = LookupTestCase.MockId(3)
        self.assertTrue(leaf.evaluate(mock0))
        mock1 = LookupTestCase.MockId(4)
        self.assertFalse(leaf.evaluate(mock1))

    def test_lookup_leaf_None(self):
        leaf = LookupLeaf(id=3)
        mock0 = LookupTestCase.MockId(3)
        self.assertTrue(leaf.evaluate(mock0))
        mock1 = LookupTestCase.MockId(4)
        self.assertFalse(leaf.evaluate(mock1))
