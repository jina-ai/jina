import threading
import time
import unittest
from multiprocessing import Process

from jina.logging import get_logger
from jina.main.parser import set_frontend_parser, set_pea_parser, set_pod_parser
from jina.peapods.pod import FrontendPod, Pod
from jina.peapods.remote import RemotePea, SpawnPodHelper, SpawnPeaHelper, SpawnDictPodHelper
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

    def test_remote_pod(self):
        f_args = set_frontend_parser().parse_args(['--allow_spawn'])
        p_args = set_pod_parser().parse_args(['--replicas', '3', '--port_grpc', str(f_args.port_grpc)])

        def start_frontend():
            with FrontendPod(f_args):
                time.sleep(5)

        t = Process(target=start_frontend)
        t.daemon = True
        t.start()

        SpawnPodHelper(p_args).start()
        t.join()

    def test_remote_two_pea(self):
        # NOTE: right now there is no way to spawn two peas with one frontend!!!
        f_args = set_frontend_parser().parse_args(['--allow_spawn'])

        def start_frontend():
            with FrontendPod(f_args):
                time.sleep(5)

        def start_client(d):
            print('im running %d' % d)
            p_args = set_pea_parser().parse_args(['--name', 'testpea%d' % d, '--port_grpc', str(f_args.port_grpc)])
            SpawnPeaHelper(p_args).start()

        t = Process(target=start_frontend)
        t.daemon = True
        t.start()

        time.sleep(1)
        c1 = Process(target=start_client, args=(1,))
        c2 = Process(target=start_client, args=(2,))
        c1.daemon = True
        c2.daemon = True

        c1.start()
        c2.start()
        time.sleep(5)
        c1.join()
        c2.join()

    def tearDown(self) -> None:
        time.sleep(2)
        super().tearDown()

    def test_customized_pod(self):
        f_args = set_frontend_parser().parse_args(['--allow_spawn'])
        p_args = set_pod_parser().parse_args(['--replicas', '3', '--port_grpc', str(f_args.port_grpc)])
        p = Pod(p_args)

        def start_frontend():
            with FrontendPod(f_args):
                time.sleep(5)

        t = Process(target=start_frontend)
        t.daemon = True
        t.start()

        SpawnDictPodHelper(p.peas_args).start()
        t.join()

    def test_remote_pea2(self):
        f_args = set_frontend_parser().parse_args(['--allow_spawn'])
        p_args = set_pea_parser().parse_args(['--host', '0.0.0.0', '--port_grpc', str(f_args.port_grpc)])

        def start_frontend():
            with FrontendPod(f_args):
                time.sleep(5)

        t = Process(target=start_frontend)
        t.daemon = True
        t.start()

        with RemotePea(p_args):
            pass
        t.join()

    def test_remote_pea(self):
        f_args = set_frontend_parser().parse_args(['--allow_spawn'])

        p_args = set_pea_parser().parse_args(['--port_grpc', str(f_args.port_grpc)])

        def start_frontend():
            with FrontendPod(f_args):
                time.sleep(5)

        t = Process(target=start_frontend)
        t.daemon = True
        t.start()

        time.sleep(1)
        SpawnPeaHelper(p_args).start()
        t.join()


if __name__ == '__main__':
    unittest.main()
