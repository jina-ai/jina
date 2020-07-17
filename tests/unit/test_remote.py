import threading
import time
import unittest

from jina.logging import get_logger
from jina.main.parser import set_gateway_parser, set_pea_parser
from jina.peapods.pod import GatewayPod
from jina.peapods.remote import PeaSpawnHelper
from tests import JinaTestCase


class MyTestCase(JinaTestCase):
    def test_logging_thread(self):
        _event = threading.Event()
        logger = get_logger('mytest', event_trigger=_event)

        def _print_messages():
            while True:
                _event.wait()
                print(f'thread: {_event.record}')
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
        logger.success('crit')
        time.sleep(.1)

    def tearDown(self) -> None:
        time.sleep(2)
        super().tearDown()

    def test_remote_not_allowed(self):
        f_args = set_gateway_parser().parse_args([])

        p_args = set_pea_parser().parse_args(['--host', 'localhost', '--port-expose', str(f_args.port_expose)])
        with GatewayPod(f_args):
            PeaSpawnHelper(p_args).start()

    def test_cont_gateway(self):
        f1_args = set_gateway_parser().parse_args(['--allow-spawn'])
        f2_args = set_gateway_parser().parse_args([])
        with GatewayPod(f1_args):
            pass

        with GatewayPod(f2_args):
            pass


if __name__ == '__main__':
    unittest.main()
