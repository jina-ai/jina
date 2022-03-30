import time
from threading import Thread

from jina import Flow


def test_borrow_same_port(port_generator):
    # hacky test but there is now good way to wait that a flow exit

    port = port_generator()

    def _flow_in_background(delay=0):
        time.sleep(delay)
        f = Flow(port=port)
        with f:
            f.block()

    t1 = Thread(target=_flow_in_background, daemon=True)
    t2 = Thread(target=_flow_in_background, args=[5], daemon=True)

    t1.start()
    t2.start()

    time.sleep(
        10
    )  # we hard wait 10 seconds and hope that the flow will close by himself during this time

    assert not t2.is_alive()
    # the second flow should exit at some point because the port is already use
    assert t1.is_alive()
