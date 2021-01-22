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


def test_dump_excutor_with_drivers(tmpdir):
    a = BaseExecutor.load_config(f'{cur_dir}/yaml/route.yml')
    a.touch()
    a._drivers['ControlRequest'][0].idle_dealer_ids = ('hello', 'there')
    a.save(str(tmpdir / 'a.bin'))

    print(a._drivers)

    b = BaseExecutor.load(str(tmpdir / 'a.bin'))
    print(b._drivers)
    assert id(b._drivers['ControlRequest'][0]) != id(a._drivers['ControlRequest'][0])

    assert not b._drivers['ControlRequest'][0].idle_dealer_ids
