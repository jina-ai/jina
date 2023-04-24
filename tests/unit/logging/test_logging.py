import glob
import os

import pytest

from jina import Document, Flow
from jina.constants import __uptime__, __windows__
from jina.enums import LogVerbosity
from jina.helper import colored
from jina.logging.logger import JinaLogger

cur_dir = os.path.dirname(os.path.abspath(__file__))


def log(logger: JinaLogger):
    logger.debug('this is test debug message')
    logger.info('this is test info message')
    logger.success('this is test success message')
    logger.warning('this is test warning message')
    logger.error('this is test error message')
    logger.critical('this is test critical message')


def test_color_log():
    with JinaLogger('test_logger') as logger:
        logger.debug('this is test debug message')
        logger.info('this is test info message')
        logger.info(f'this is test {colored("color", "red")} message')
        logger.success('this is test success message')
        logger.warning('this is test warning message')
        logger.error('this is test error message')
        logger.critical('this is test critical message')


def test_logging_syslog():
    with JinaLogger(
        'test_logger', log_config=os.path.join(cur_dir, 'yaml/syslog.yml')
    ) as logger:
        log(logger)
        assert len(logger.handlers) == 0 if __windows__ else 1


def test_logging_default():
    import logging
    import sys

    with JinaLogger('test_logger') as logger:
        log(logger)
        assert len(logger.handlers) == 1

    # test whether suppress root handlers
    logging.root.handlers.append(logging.StreamHandler(sys.stdout))
    with JinaLogger('test_logger', suppress_root_logging=False) as logger:
        log(logger)
        assert len(logging.root.handlers) > 0


def test_logging_level_yaml(monkeypatch):
    monkeypatch.delenv('JINA_LOG_LEVEL', raising=True)  # ignore global env
    fn = os.path.join(cur_dir, f'jina-{__uptime__}.log')
    with JinaLogger(
        'test_file_logger', log_config=os.path.join(cur_dir, 'yaml/file.yml')
    ) as file_logger:
        if os.path.exists(fn):
            os.remove(fn)
        log(file_logger)
        assert file_logger.logger.level == LogVerbosity.from_string('INFO')
    for f in glob.glob(cur_dir + '/*.log'):
        os.remove(f)


def test_logging_file(monkeypatch):
    monkeypatch.delenv('JINA_LOG_LEVEL', raising=True)  # ignore global env
    uptime = __uptime__.replace(':', '.') if __windows__ else __uptime__
    fn = os.path.join(cur_dir, f'jina-{uptime}.log')
    with JinaLogger(
        'test_file_logger', log_config=os.path.join(cur_dir, 'yaml/file.yml')
    ) as file_logger:
        log(file_logger)
        assert os.path.exists(fn)
        with open(fn, encoding='utf-8') as fp:
            assert len(fp.readlines()) == 5
    for f in glob.glob(cur_dir + '/*.log'):
        os.remove(f)


@pytest.mark.slow
def test_logging_quiet(caplog):
    # no way to capture logs in multiprocessing
    # see discussion here: https://github.com/pytest-dev/pytest/issues/3037#issuecomment-745050393

    f = Flow().add(quiet=True).add()
    with f:
        f.index(Document())
