import os
import pickle

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
    print(f'\n\nexecutor_a._drivers={executor_a._drivers}\n\n')

    # load the saved executor_a as executor_b
    executor_b = BaseExecutor.load(str(tmpdir / 'aux.bin')) 
    assert hasattr(executor_b, '_drivers') is False
    
