import os

import pytest
from jina import __uptime__
from jina.logging import JinaLogger

cur_dir = os.path.dirname(os.path.abspath(__file__))


def log(logger):
    logger.debug('this is test debug message')
    logger.info('this is test info message')
    logger.success('this is test success message')
    logger.warning('this is test warning message')
    logger.error('this is test error message')
    logger.critical('this is test critical message')


def test_logging_syslog():
    with JinaLogger('test_logger', log_config=os.path.join(cur_dir, 'yaml/syslog.yml')) as logger:
        log(logger)
        assert len(logger.handlers) == 1


def test_logging_default():
    with JinaLogger('test_logger') as logger:
        log(logger)
        try:
            import fluent
            assert len(logger.handlers) == 3
        except (ModuleNotFoundError, ImportError):
            # if fluent not installed
            assert len(logger.handlers) == 2


def test_logging_file():
    with JinaLogger('test_logger', log_config=os.path.join(cur_dir, 'yaml/file.yml')) as logger:
        log(logger)
    assert os.path.exists(f'jina-{__uptime__}.log')
    with open(f'jina-{__uptime__}.log') as fp:
        assert len(fp.readlines()) == 5


@pytest.mark.parametrize('log_config', ['yaml/fluent.yml', None])
def test_logging_fluentd(monkeypatch, log_config):
    from fluent import asynchandler as fluentasynchandler
    with JinaLogger('test_logger', log_config=log_config, group_id='test_group_id') as logger:
        def mock_emit(obj, record):
            msg = obj.format(record)
            assert msg['group_id'] == 'test_group_id'
            assert msg['context'] == 'test_logger'
            assert msg['type'] == 'INFO'
            assert msg['message'] == 'logging progress'

        monkeypatch.setattr(fluentasynchandler.FluentHandler, "emit", mock_emit)
        logger.info('logging progress')
