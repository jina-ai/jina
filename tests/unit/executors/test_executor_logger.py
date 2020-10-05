import pytest
from jina.parser import set_pea_parser
from jina.executors import BaseExecutor
from jina.executors.metas import get_default_metas


@pytest.fixture(scope='function', autouse=True)
def metas(tmpdir):
    metas = get_default_metas()
    metas['workspace'] = str(tmpdir)
    yield metas


def test_executor_logger(metas):
    from fluent import asynchandler as fluentasynchandler
    args = set_pea_parser().parse_args(['--log-sse'])
    with BaseExecutor(args, metas=metas) as executor:
        assert args.log_sse
        assert len(executor.logger.logger.handlers) == 2
        assert isinstance(executor.logger.logger.handlers[0], fluentasynchandler.FluentHandler)
        executor.logger.info('logging from executor')
        executor.touch()
        executor.save()
        save_abspath = executor.save_abspath

    with BaseExecutor.load(save_abspath) as executor:
        assert executor.args.log_sse
        assert len(executor.logger.logger.handlers) == 2
        assert isinstance(executor.logger.logger.handlers[0], fluentasynchandler.FluentHandler)
        executor.logger.info('logging from executor')
