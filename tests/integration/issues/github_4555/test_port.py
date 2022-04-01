import time
from threading import Thread

import pytest

from jina import Flow
from jina.excepts import PortAlreadyUsed


def test_two_flow_using_on_same_port_failing(port_generator):
    # hacky test but there is now good way to wait that a flow exit

    port = port_generator()

    f1 = Flow(port=port)
    f2 = Flow(port=port)

    with f1:
        with pytest.raises(PortAlreadyUsed):
            with f2:
                pass


def test_two_flow_using_on_same_build_succed(port_generator):
    # hacky test but there is now good way to wait that a flow exit

    port = port_generator()

    f1 = Flow(port=port)
    f2 = Flow(port=port)

    with f1:
        f2.build()
        with pytest.raises(PortAlreadyUsed):
            with f2:
                pass
