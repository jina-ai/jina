import grpc

from .pea import Pea
from ..helper import PathImporter


class GRPCService(Pea):

    def load_executor(self):
        super().load_executor()
        self.channel = grpc.insecure_channel(
            '%s:%s' % (self.args.host, self.args.port_grpc),
            options=[('grpc.max_send_message_length', self.args.max_message_size),
                     ('grpc.max_receive_message_length', self.args.max_message_size)])

        m = PathImporter.add_modules(self.args.pb2_path, self.args.pb2_grpc_path)

        # build stub
        self.stub = getattr(m, self.args.stub_name)(self.channel)

    def close_executor(self):
        self.channel.close()
