from jina.drivers.control import SplitRouteDriver, split_message_by_mode_id
from jina.proto import jina_pb2
from jina.peapods.pea import BasePea
from tests import JinaTestCase


def create_message_with_3_modes():
    # Create documents od different modes
    # Put them in a message
    envelope = jina_pb2.Envelope()
    envelope.receiver_id = 'receiver'
    envelope.sender_id = 'sender'
    req = jina_pb2.Request()
    req.request_id = 1
    d_mode_1 = req.index.docs.add()
    d_mode_1.id = 0
    d_mode_1.mode_id = 0
    d_mode_1.mime_type = 'text/plain'
    d_mode_2 = req.index.docs.add()
    d_mode_2.id = 1
    d_mode_2.mode_id = 1
    d_mode_2.mime_type = 'image/png'
    d_mode_3 = req.index.docs.add()
    d_mode_3.id = 2
    d_mode_3.mode_id = 2
    d_mode_3.mime_type = 'image/png'
    msg = jina_pb2.Message()
    msg.envelope.CopyFrom(envelope)
    msg.request.CopyFrom(req)
    return msg


class SplitRouteDriverTestCase(JinaTestCase):
    class MockPea(BasePea):
        class MockZmqlet:
            def pause_pollin(self):
                pass

            def resume_pollin(self):
                pass

        def __init__(self, args=None):
            super().__init__(args)
            self.zmqlet = SplitRouteDriverTestCase.MockPea.MockZmqlet()

    def test_split_messages_by_mode_id(self):
        msg = create_message_with_3_modes()
        output_msgs = split_message_by_mode_id(msg, 3)
        self.assertEqual(len(output_msgs), 3)
        self.assertEqual(len(output_msgs[0].request.index.docs), 1)
        self.assertEqual(output_msgs[0].request.index.docs[0].mode_id, 0)
        self.assertEqual(len(output_msgs[1].request.index.docs), 1)
        self.assertEqual(output_msgs[1].request.index.docs[0].mode_id, 1)
        self.assertEqual(len(output_msgs[2].request.index.docs), 1)
        self.assertEqual(output_msgs[2].request.index.docs[0].mode_id, 2)

        self.assertEqual(output_msgs[0].envelope, msg.envelope)
        self.assertEqual(output_msgs[1].envelope, msg.envelope)
        self.assertEqual(output_msgs[2].envelope, msg.envelope)

    def test_split_router_driver_simple(self):
        pea = SplitRouteDriverTestCase.MockPea(None)
        driver = SplitRouteDriver(num_modes=3)
        driver.attach(pea)
        msg = create_message_with_3_modes()
        pea._message_in = msg
        pea._request = getattr(msg.request, 'index')
        driver.idle_dealer_ids[0] = 'idle_0'
        driver.idle_dealer_ids[1] = 'idle_1'
        driver.idle_dealer_ids[2] = 'idle_0'

        driver()

        self.assertEqual(len(driver.output_msgs), 3)
        self.assertEqual(len(driver.output_msgs[0].request.index.docs), 1)
        self.assertEqual(driver.output_msgs[0].request.index.docs[0].mode_id, 0)
        self.assertEqual(len(driver.output_msgs[1].request.index.docs), 1)
        self.assertEqual(driver.output_msgs[1].request.index.docs[0].mode_id, 1)
        self.assertEqual(len(driver.output_msgs[2].request.index.docs), 1)
        self.assertEqual(driver.output_msgs[2].request.index.docs[0].mode_id, 2)

        self.assertEqual(driver.output_msgs[0].envelope.sender_id, msg.envelope.sender_id)
        self.assertEqual(driver.output_msgs[1].envelope.sender_id, msg.envelope.sender_id)
        self.assertEqual(driver.output_msgs[2].envelope.sender_id, msg.envelope.sender_id)
        self.assertEqual(driver.output_msgs[0].envelope.receiver_id, 'idle_0')
        self.assertEqual(driver.output_msgs[1].envelope.receiver_id, 'idle_1')
        self.assertEqual(driver.output_msgs[2].envelope.receiver_id, 'idle_0')
