import pytest

from jina.jaml.parsers.executor.legacy import ExecutorLegacyParser


class A00:
    def __init__(self, a00):
        self.a00 = a00


class A0(A00):
    def __init__(self, a0):
        self.a0 = a0


class A(A0):
    def __init__(self, a):
        self.a = a


class B:
    def __init__(self, b):
        self.b = b


class C:
    def __init__(self, c):
        self.c = c


class E(A, B, C):
    pass


class D(A, B, C):
    def __init__(self, d, *args, **kwargs):
        super.__init__(*args, **kwargs)
        self.d = d


class A_dummy:
    pass


D_arguments = {'a00', 'a0', 'a', 'b', 'c', 'd', 'self', 'args', 'kwargs'}
E_arguments = {'a00', 'a0', 'a', 'b', 'c', 'self', 'args', 'kwargs'}
A_dummy_arguments = {'self', 'args', 'kwargs'}


@pytest.mark.parametrize(
    'input_class, expected_arguments',
    [(E, E_arguments), (D, D_arguments), (A_dummy, A_dummy_arguments)],
)
def test_get_all_arguments(input_class, expected_arguments):
    """
    Tests ExecutorLegacyParser._get_all_arguments retriving all arguments from a class and any class it inherits from
    """
    arguments_from_cls = ExecutorLegacyParser._get_all_arguments(class_=input_class)
    assert arguments_from_cls == expected_arguments
