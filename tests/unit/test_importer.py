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
    assert (not depend_tree) == import_once


@pytest.mark.parametrize('import_once', [True, False])
def test_import_classes_import_once_exception(import_once):
    with pytest.raises(TypeError):
        _ = import_classes(namespace='dummy', import_once=import_once)


@pytest.mark.parametrize('ns', ['jina.executors', 'jina.hub', 'jina.drivers'])
def test_import_classes_failed_find_package(ns, mocker):
    mocker.patch('pkgutil.get_loader', return_value=None)
    depend_tree = import_classes(namespace=ns)
    assert len(depend_tree) == 0


@pytest.mark.parametrize('ns', ['jina.executors', 'jina.hub', 'jina.drivers'])
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


@pytest.mark.parametrize('print_table', [True, False])
@pytest.mark.parametrize('ns', ['jina.executors', 'jina.hub'])
def test_import_classes_failed_load_default_exc_config(
    ns, print_table, mocker, recwarn, capsys
):
    mocker.patch('pkg_resources.resource_stream', side_effect=Exception('mocked error'))
    _ = import_classes(namespace=ns, show_import_table=print_table)
    if print_table:
        captured = capsys.readouterr()
        assert '✗' in captured.out
    else:
        assert len(recwarn) == 1
        assert (
            'You can use `jina check` to list all executors and drivers'
            in recwarn[0].message.args[0]
        )
