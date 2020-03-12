import threading
import time
import unittest
from multiprocessing import Process

from jina.clients.python import SpawnPeaPyClient, SpawnPodPyClient, SpawnDictPodPyClient
from jina.logging import get_logger
from jina.main.parser import set_frontend_parser, _set_grpc_parser, set_pea_parser, set_pod_parser
from jina.peapods.pod import FrontendPod, Pod
from tests import JinaTestCase


class MyTestCase(JinaTestCase):
    def test_logging_thread(self):
        _event = threading.Event()
        logger = get_logger('mytest', log_event=_event)

        def _print_messages():
            while True:
                _event.wait()
                print('thread: %s' % _event.record)
                print(type(_event.record))
                _event.clear()

        t = threading.Thread(target=_print_messages)
        t.daemon = True
        t.start()

        logger.info('blah, blah')
        logger.info('blah, blah, blah')
        time.sleep(.1)
        logger.warning('warn, warn, warn')
        time.sleep(.1)
        logger.debug('warn, warn, warn')
        time.sleep(.1)
        logger.critical('crit')
        time.sleep(.1)

    def tearDown(self) -> None:
        time.sleep(2)
        super().tearDown()

    def test_remote_not_allowed(self):
        f_args = set_frontend_parser().parse_args([])
        c_args = _set_grpc_parser().parse_args(['--grpc_port', str(f_args.grpc_port)])
        p_args = set_pea_parser().parse_args([])
        with FrontendPod(f_args):
            SpawnPeaPyClient(c_args, p_args).start()

    def test_remote_pea(self):
        f_args = set_frontend_parser().parse_args(['--allow_spawn'])
        c_args = _set_grpc_parser().parse_args(['--grpc_port', str(f_args.grpc_port)])
        p_args = set_pea_parser().parse_args([])

        def start_frontend():
            with FrontendPod(f_args):
                time.sleep(5)

        t = Process(target=start_frontend)
        t.daemon = True
        t.start()

        time.sleep(1)
        SpawnPeaPyClient(c_args, p_args).start()

    def test_remote_pod(self):
        f_args = set_frontend_parser().parse_args(['--allow_spawn'])
        c_args = _set_grpc_parser().parse_args(['--grpc_port', str(f_args.grpc_port)])
        p_args = set_pod_parser().parse_args(['--replicas', '3'])

        def start_frontend():
            with FrontendPod(f_args):
                time.sleep(5)

        t = Process(target=start_frontend)
        t.daemon = True
        t.start()

        SpawnPodPyClient(c_args, p_args).start()

    def test_customized_pod(self):
        f_args = set_frontend_parser().parse_args(['--allow_spawn'])
        c_args = _set_grpc_parser().parse_args(['--grpc_port', str(f_args.grpc_port)])
        p_args = set_pod_parser().parse_args(['--replicas', '3'])
        p = Pod(p_args)

        def start_frontend():
            with FrontendPod(f_args):
                time.sleep(5)

        t = Process(target=start_frontend)
        t.daemon = True
        t.start()

        SpawnDictPodPyClient(c_args, p.peas_args).start()


if __name__ == '__main__':
    unittest.main()
