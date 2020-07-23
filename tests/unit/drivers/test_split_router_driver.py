import os
import pytest

import numpy as np
from jina.drivers.control import SplitRouteDriver
from jina.drivers.helper import array2pb
from jina.proto.jina_pb2 import Document, Message, Envelope
from jina.peapods.pea import BasePea
from tests import JinaTestCase

cur_dir = os.path.dirname(os.path.abspath(__file__))

class SplitRouteDriverTestCase(JinaTestCase):
    class MockPea(BasePea):
        def __init__(self, args=None):
            super().__init__(args)

    @pytest.mark.skip('Fix it')
    def test_split_router_driver_simple(self):
        pea = SplitRouteDriverTestCase.MockPea(None)
        driver = SplitRouteDriver(num_modes=2)
        driver.attach(pea)

        d_mode_1 = Document()
        d_mode_1.mode_id = 0
        d_mode_1.mime_type = 'text/plain'
        d_mode_1.blob.CopyFrom(array2pb(np.ndarray([0, 0, 0])))
        d_mode_2 = Document()
        d_mode_2.mode_id = 1
        d_mode_2.mime_type = 'image/png'
        d_mode_2.blob.CopyFrom(array2pb(np.ndarray([1, 1, 1])))

        msg = Message()
        msg.envelope = Envelope()
        msg.request.docs.append(d_mode_1)
        msg.request.docs.append(d_mode_2)

        pea._message_in = msg
        pea._request = msg.request
        driver.idle_dealer_ids[0] = 0
        driver.idle_dealer_ids[1] = 1

        driver()

        self.assertTrue(len(driver.output_msgs), 2)
        self.assertTrue(len(driver.output_msgs[0].req.docs), 1)
        self.assertTrue(driver.output_msgs[0].req.docs[0].mode_id, 0)
        self.assertTrue(len(driver.output_msgs[1].req.docs), 1)
        self.assertTrue(driver.output_msgs[1].req.docs[0].mode_id, 1)

        self.assertTrue(driver.output_msgs[0].envelope.receiver_id, 0)
        self.assertTrue(driver.output_msgs[1].envelope.receiver_id, 1)
