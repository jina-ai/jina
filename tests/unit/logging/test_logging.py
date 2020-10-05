import os

from jina.logging.base import get_logger


def test_logging_message():
    old_log_level = os.getenv('JINA_LOG_VERBOSITY')
    os.environ['JINA_LOG_VERBOSITY'] = 'success'
    logger = get_logger('test_logger')
    logger.debug('this is test debug message')
    logger.info('this is test info message')
    logger.success('this is test success message')
    logger.warning('this is test warning message')
    logger.error('this is test error message')
    logger.critical('this is test critical message')
    if old_log_level:
        os.environ['JINA_LOG_VERBOSITY'] = old_log_level
    else:
        del os.environ['JINA_LOG_VERBOSITY']
