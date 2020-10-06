import pytest

from jina.executors import BaseExecutor
from jina.executors.metas import get_default_metas
from jina.parser import set_pea_parser


@pytest.fixture(scope='function', autouse=True)
def metas(tmpdir):
    metas = get_default_metas()
    metas['workspace'] = str(tmpdir)
    yield metas


def test_executor_logger(metas):
    from fluent import asynchandler as fluentasynchandler
    args = set_pea_parser().parse_args([])
    with BaseExecutor(args, metas=metas) as executor:
        assert len(executor.logger.logger.handlers) == 3
        has_fluent = False
        for h in executor.logger.logger.handlers:
            if isinstance(h, fluentasynchandler.FluentHandler):
                has_fluent = True
        assert has_fluent
        executor.logger.info('logging from executor')
        executor.touch()
        executor.save()
        save_abspath = executor.save_abspath

    with BaseExecutor.load(save_abspath) as executor:
        assert len(executor.logger.logger.handlers) == 3
        has_fluent = False
        for h in executor.logger.logger.handlers:
            if isinstance(h, fluentasynchandler.FluentHandler):
                has_fluent = True
        assert has_fluent
        executor.logger.info('logging from executor')
