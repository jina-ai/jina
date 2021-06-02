import copy
import threading
import time
import zmq


def get_next_targets(routes):
    next_routes = {}
    next_targets = routes[0]
    if not isinstance(next_targets, list):
        next_targets = [next_targets]
    remaining_routes = routes[1:]
    for next_target in next_targets:
        if isinstance(next_target, list):
            next_pod = next_target[0]
            next_routes[next_pod] = next_target[1:] + remaining_routes
        else:
            next_routes[next_target] = remaining_routes
    return next_routes


class HeadPea:
    def __init__(self, in_socket):
        self._in_socket = in_socket
        self.context = zmq.Context()
        self.routes = {}
        self.receiver = self.context.socket(zmq.ROUTER)
        self.receiver.bind(self._in_socket)

    def run(self):
        while True:
            self.receiver.recv()
            message = self.receiver.recv_json()

            self.do_work(message)
            self.post(message)

    def do_work(self, message):
        message['content'] += self._in_socket
        return

    def post(self, message):
        routes = message['routes']
        if routes:
            next_routes = get_next_targets(routes)
        else:
            print(
                f"Last HeadPea reached: {self._in_socket}. Final content: {message['content']}"
            )
            return
        for next_target, downstream in next_routes.items():
            if next_target not in self.routes:
                new_socket = self.context.socket(zmq.DEALER)
                new_socket.connect(next_target)
                self.routes[next_target] = new_socket

            next_message = copy.deepcopy(message)
            next_message['routes'] = downstream

            self.routes[next_target].send_json(next_message)


def pea_starter(pea_id, context=None):
    context = context or zmq.Context.instance()
    HeadPea(pea_id).run()


def main():
    print("Starting")

    pea_ids = [f'tcp://*:{port}' for port in range(5672, 5679)]
    for pea_id in pea_ids:
        thread = threading.Thread(target=pea_starter, args=(pea_id,))
        thread.daemon = True
        thread.start()
    gateway = HeadPea('tcp://*:5670')
    message = {
        'routes': [
            ['tcp://localhost:5672', 'tcp://localhost:5674'],
            'tcp://localhost:5673',
            'tcp://localhost:5675',
            ['tcp://localhost:5673', 'tcp://localhost:5674'],
            'tcp://localhost:5676',
            'tcp://localhost:5677',
            'tcp://localhost:5678',
        ],
        'content': '',
    }

    for i in range(1):
        gateway.post(message)

    print("All messages send")
    time.sleep(5)
    print("Shutting down")


if __name__ == '__main__':
    main()


def test_single_routing():
    next_routes = get_next_targets(['1'])
    assert next_routes == {'1': []}


def test_simple_routing():
    next_routes = get_next_targets(['1', '2'])
    assert next_routes == {'1': ['2']}


def test_long_routing():
    next_routes = get_next_targets(['1', '2', '3', '4'])
    assert next_routes == {'1': ['2', '3', '4']}


def test_double_routing():
    next_routes = get_next_targets([['1', '3'], '2'])
    assert next_routes == {'1': ['2'], '3': ['2']}


def test_nested_routing():
    next_routes = get_next_targets([[['1', '4'], '3'], '2'])
    assert next_routes == {'1': ['4', '2'], '3': ['2']}


def test_complex_routing():
    next_routes = get_next_targets([[['1', ['4', '5']], '3'], '2'])
    assert next_routes == {'1': [['4', '5'], '2'], '3': ['2']}


def test_complex_routing2():
    next_routes = get_next_targets([[['1', ['4', '5']], '3'], '2'])
    assert next_routes == {'1': [['4', '5'], '2'], '3': ['2']}
