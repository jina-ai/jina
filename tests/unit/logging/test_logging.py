from jina.logging import JinaLogger
import os
from jina import __uptime__


def log(logger):
    logger.debug('this is test debug message')
    logger.info('this is test info message')
    logger.success('this is test success message')
    logger.warning('this is test warning message')
    logger.error('this is test error message')
    logger.critical('this is test critical message')


def test_logging_syslog():
    logger = JinaLogger('test_logger', config_path='yaml/syslog.yml')
    log(logger)


def test_logging_default():
    logger = JinaLogger('test_logger')
    log(logger)


def test_logging_file():
    logger = JinaLogger('test_logger', config_path='yaml/file.yml')
    log(logger)
    assert os.path.exists(f'jina-{__uptime__}.log')
    with open(f'jina-{__uptime__}.log') as fp:
        assert len(fp.readlines()) == 5
