import os
import pickle
import pytest 

from jina.drivers.control import RouteDriver
from jina.executors import BaseExecutor

cur_dir = os.path.dirname(os.path.abspath(__file__))

def test_dump_driver(tmpdir):
    rd = RouteDriver(raise_no_dealer=True)
    rd.idle_dealer_ids = ('hello', 'there')

    with open(str(tmpdir / 'a.bin'), 'wb') as fp:
        pickle.dump(rd, fp)

    with open(str(tmpdir / 'a.bin'), 'rb') as fp:
        p = pickle.load(fp)

    # init args & kwargs values should be save
    assert p.raise_no_dealer

    # other stateful values should be reset to init()'s time
    assert not p.idle_dealer_ids

def test_dump_excutor_without_drivers(tmpdir):

    # Create an executor from a yaml file and store it to disc 
    executor_a = BaseExecutor.load_config(f'{cur_dir}/yaml/route.yml')
    executor_a.touch()
    executor_a._drivers['ControlRequest'][0].idle_dealer_ids = ('hello', 'there')
    executor_a.save(str(tmpdir / 'aux.bin'))

    # load the saved executor_a as executor_b
    executor_b = BaseExecutor.load(str(tmpdir / 'aux.bin')) 
    assert hasattr(executor_b, '_drivers') is False


@pytest.fixture
def temp_workspace(tmpdir):
    os.environ['JINA_TEST_LOAD_FROM_DUMP_WORKSPACE'] = str(tmpdir)
    yield
    del os.environ['JINA_TEST_LOAD_FROM_DUMP_WORKSPACE']


def test_drivers_renewed_from_yml_when_loaded_from_dump(temp_workspace):
    executor_a = BaseExecutor.load_config(f'{cur_dir}/yaml/example_1.yml')
    assert executor_a._drivers['SearchRequest'][0]._is_update is True

    with executor_a:
        executor_a.touch()

    executor_b = BaseExecutor.load_config(f'{cur_dir}/yaml/example_2.yml')
    assert executor_b._drivers['SearchRequest'][0]._is_update is False