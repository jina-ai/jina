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


@pytest.mark.parametrize('ns', ['jina.executors', 'jina.hub'])
def test_import_classes_failed_find_package(ns, mocker):
    mocker.patch('pkgutil.get_loader', return_value=None)
    depend_tree = import_classes(namespace=ns)
    assert len(depend_tree) == 0


@pytest.mark.parametrize('ns', ['jina.executors', 'jina.hub'])
def test_import_classes_failed_import_module(ns, mocker, recwarn):
    import importlib

    mocker.patch.object(
        importlib, 'import_module', side_effect=Exception('mocked error')
    )
    depend_tree = import_classes(namespace=ns)
    assert len(depend_tree) == 0
    assert len(recwarn) == 1
    assert (
        'You can use `jina check` to list all executors and drivers'
        in recwarn[0].message.args[0]
    )
