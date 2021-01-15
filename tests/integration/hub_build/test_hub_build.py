import pytest
import os

from jina import Flow

from jina.executors import BaseExecutor

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='function')
def executor_classes():
    """List all executors inherited from :class:``BaseExecutor``."""
    executors = set()
    work = [BaseExecutor]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in executors:
                executors.add(child)
                work.append(child)
    return executors


@pytest.fixture(scope='function')
def test_setups(executor_classes):
    """Prepare a list of executor driver pairs."""
    executors_drivers = []
    for ExecutorCls in executor_classes:
        try:
            drivers = ExecutorCls.default_drivers()
            for DriverCls in drivers:
                executors_drivers.append((ExecutorCls, DriverCls))
        except AttributeError:
            # TODO REMOVE AFTER ALL CLASSES HAS DEFAULT DRIVERS
            continue
    return executors_drivers


def test_a(test_setups):
    for Executor, Driver in test_setups:
        # TODO POC WITH BaseImageEncoder & EncodeDriver
        if 'BaseImageEncoder' in str(Executor):
            print(f'{Executor} corresponded driver is {Driver}')
            # TODO FIX THIS
            driver_name = str(Driver).split('.')[-1][:-2]
            executor_name = str(Executor).split('.')[-1][:-2]
            print(Driver)
            print(Executor)
            empty = '{}'
            yaml = f'''
!{executor_name}
with:
  {empty}
requests:
  on:
    [IndexRequest, SearchRequest]:
      - !{driver_name} {empty}
            '''
            print(yaml) # TODO dump it
            with Flow().add(uses='test.yml'):
                pass



