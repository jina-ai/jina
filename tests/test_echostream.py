from tests import JinaTestCase


class MyTestCase(JinaTestCase):

    def test_echostream(self):
        import zmq
        from zmq.eventloop import zmqstream
        import tornado.ioloop

        io_loop = tornado.ioloop.IOLoop.current()

        ctx = zmq.Context()
        s = ctx.socket(zmq.ROUTER)
        s.bind('tcp://127.0.0.1:5555')
        stream = zmqstream.ZMQStream(s, io_loop)

        def echo(msg):
            print(" ".join(map(repr, msg)))
            stream.send_multipart(msg)

        stream.on_recv(echo)
        io_loop.start()

