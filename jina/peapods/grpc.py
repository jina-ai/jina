__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import grpc

from .pea import BasePea
from ..importer import PathImporter


class GRPCService(BasePea):

    def load_executor(self):
        super().load_executor()
        self.channel = grpc.insecure_channel(
            f'{self.args.host}:{self.args.port_expose}',
            options=[('grpc.max_send_message_length', self.args.max_message_size),
                     ('grpc.max_receive_message_length', self.args.max_message_size)])

        m = PathImporter.add_modules(self.args.pb2_path, self.args.pb2_grpc_path)

        # build stub
        self.stub = getattr(m, self.args.stub_name)(self.channel)

    def close_executor(self):
        self.channel.close()
