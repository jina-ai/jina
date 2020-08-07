from tests import JinaTestCase
from jina.helper import cached_property


class MyTestCase(JinaTestCase):
    def test_cached_property(self):
        class Foo:
            def __init__(self):
                self._counter = 0

            @cached_property
            def counter(self):
                self._counter += 1
                return self.get_counter()

            def get_counter(self):
                return self._counter

        foo = Foo()
        # counter should not increase
        for _ in range(5):
            self.assertEqual(foo.counter, 1)

