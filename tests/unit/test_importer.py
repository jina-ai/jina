import pytest

from jina.importer import ImportExtensions
from jina.logging.predefined import default_logger


def test_bad_import():
    from jina.logging.predefined import default_logger

    with pytest.raises(ModuleNotFoundError):
        with ImportExtensions(required=True, logger=default_logger):
            import abcdefg  # no install and unlist

    with pytest.raises(ModuleNotFoundError):
        with ImportExtensions(required=True, logger=default_logger):
            import ngt  # list but no install

    fake_tags = ['ngt', 'index', 'py37']
    with ImportExtensions(required=False, logger=default_logger) as ie:
        ie._tags = fake_tags
        import ngt

    assert ie._tags == fake_tags

    with ImportExtensions(required=False, logger=default_logger) as ie:
        ie._tags = fake_tags
        import ngt.abc.edf

    assert ie._tags == fake_tags

    with ImportExtensions(required=False, logger=default_logger) as ie:
        ie._tags = fake_tags
        from ngt.abc import edf

    assert ie._tags == fake_tags

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
