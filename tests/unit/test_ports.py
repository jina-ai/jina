from jina.helper import register_port, get_registered_ports, deregister_all_ports
from tests import JinaTestCase


class MyTestCase(JinaTestCase):

    def test_port_registration(self):
        register_port(5555)
        register_port(5556)
        register_port(5557)
        register_port(5555)

        assert get_registered_ports() == [5555, 5556, 5557]
        deregister_all_ports()
        assert get_registered_ports() == []
