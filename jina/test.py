
def test_docstring_check_success(param1: str) -> bool:
    """
    Check docsting using darglint.

    :param param1: A test parameter.
    :return: Return `True` if length of parameter is above 5, else `False`.
    """
    if len(param1) > 5:
        return True
    else:
        return False


def test_docstring_check_fail(param1: str) -> bool:
    """
    Check docsting using darglint, missing parameter and return section.
    """
    if len(param1) > 5:
        return True
    else:
        return False