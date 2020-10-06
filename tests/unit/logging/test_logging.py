import os

from jina import __uptime__
from jina.logging import JinaLogger


def log(logger):
    logger.debug('this is test debug message')
    logger.info('this is test info message')
    logger.success('this is test success message')
    logger.warning('this is test warning message')
    logger.error('this is test error message')
    logger.critical('this is test critical message')


def test_logging_syslog():
    with JinaLogger('test_logger', log_config='yaml/syslog.yml') as logger:
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
    with JinaLogger('test_logger', log_config='yaml/file.yml') as logger:
        log(logger)
    assert os.path.exists(f'jina-{__uptime__}.log')
    with open(f'jina-{__uptime__}.log') as fp:
        assert len(fp.readlines()) == 5


