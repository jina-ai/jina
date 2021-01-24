import pytest

from jina.importer import ImportExtensions, import_classes
from jina.logging import default_logger


def test_bad_import():
    from jina.logging import default_logger

    with pytest.raises(ModuleNotFoundError):
        with ImportExtensions(required=True, logger=default_logger):
            import abcdefg  # no install and unlist

    with pytest.raises(ModuleNotFoundError):
        with ImportExtensions(required=True, logger=default_logger):
            import ngt  # list but no install

    with ImportExtensions(required=False, logger=default_logger) as ie:
        import ngt

    assert ie._tags == ['ngt', 'index', 'py37']

    with ImportExtensions(required=False, logger=default_logger) as ie:
        import ngt.abc.edf

    assert ie._tags == ['ngt', 'index', 'py37']

    with ImportExtensions(required=False, logger=default_logger) as ie:
        from ngt.abc import edf

    assert ie._tags == ['ngt', 'index', 'py37']

    with ImportExtensions(required=False, logger=default_logger) as ie:
        import abcdefg

    assert not ie._tags


def test_no_suppress_other_exception():
    with pytest.raises(Exception):
        with ImportExtensions(required=False, logger=default_logger):
            raise Exception

    with pytest.raises(Exception):
        with ImportExtensions(required=True, logger=default_logger):
            raise Exception


@pytest.mark.parametrize('import_once', [True, False])
@pytest.mark.parametrize('ns', ['jina.executors', 'jina.hub', 'jina.drivers'])
def test_import_classes_import_once(ns, import_once):
    depend_tree = import_classes(namespace=ns, import_once=import_once)
    assert (depend_tree is None) == import_once


@pytest.mark.parametrize('import_once', [True, False])
def test_import_classes_import_once_exception(import_once):
    with pytest.raises(TypeError):
        _ = import_classes(namespace='dummy', import_once=import_once)


@pytest.mark.parametrize('ns', ['jina.executors', 'jina.hub', 'jina.drivers'])
def test_import_classes_failed_find_package(ns, mocker):
    import pkgutil
    mocker.patch.object(pkgutil, 'get_loader', return_value=None)
    depend_tree = import_classes(namespace=ns)
    assert not depend_tree
