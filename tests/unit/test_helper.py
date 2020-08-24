import unittest

from jina.helper import cached_property
from tests import JinaTestCase


class MyTestCase(JinaTestCase):

    def test_cached_property(self):
        """Test the cached_property decorator"""
        new_value = "99999"

        class TestClass:
            def __init__(self):
                self.value = "11111"

            def change_value_in_instance(self, value):
                self.value = value

            @cached_property
            def test_property(self):
                return self.value

            @property
            def test_uncached_property(self):
                return self.value

        testClass = TestClass()
        first_cached_test_property = testClass.test_property
        first_uncached_test_property = testClass.test_uncached_property
        testClass.change_value_in_instance(new_value)
        second_cached_test_property = testClass.test_property
        second_uncached_test_property = testClass.test_uncached_property

        assert first_cached_test_property == second_cached_test_property
        assert first_cached_test_property == "11111"

        self.assertNotEqual(first_uncached_test_property, second_uncached_test_property)
        assert first_uncached_test_property == "11111"
        assert second_uncached_test_property == "99999"


if __name__ == "__main__":
    unittest.main()
