import os
import unittest

from jina.enums import SocketType
from jina.flow import Flow
from tests import JinaTestCase

cur_dir = os.path.dirname(os.path.abspath(__file__))


class FlowFacesExamplesTestCase(JinaTestCase):

    def test_index(self):
        f = Flow.load_config(os.path.join(cur_dir, '../yaml/examples/faces/flow-index.yml'))
        with f:
            node = f._pod_nodes['gateway']
            self.assertEqual(node.head_args.socket_in, SocketType.PULL_CONNECT)
            self.assertEqual(node.tail_args.socket_out, SocketType.PUSH_CONNECT)

            node = f._pod_nodes['loader']
            self.assertEqual(node.head_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.head_args.socket_out, SocketType.ROUTER_BIND)
            for arg in node.peas_args['peas']:
                self.assertEqual(arg.socket_in, SocketType.DEALER_CONNECT)
                self.assertEqual(arg.socket_out, SocketType.PUSH_CONNECT)
            self.assertEqual(node.tail_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.tail_args.socket_out, SocketType.PUB_BIND)

            node = f._pod_nodes['flipper']
            self.assertEqual(node.head_args.socket_in, SocketType.SUB_CONNECT)
            self.assertEqual(node.head_args.socket_out, SocketType.ROUTER_BIND)
            for arg in node.peas_args['peas']:
                self.assertEqual(arg.socket_in, SocketType.DEALER_CONNECT)
                self.assertEqual(arg.socket_out, SocketType.PUSH_CONNECT)
            self.assertEqual(node.tail_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.tail_args.socket_out, SocketType.PUSH_CONNECT)

            node = f._pod_nodes['normalizer']
            self.assertEqual(node.head_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.head_args.socket_out, SocketType.ROUTER_BIND)
            for arg in node.peas_args['peas']:
                self.assertEqual(arg.socket_in, SocketType.DEALER_CONNECT)
                self.assertEqual(arg.socket_out, SocketType.PUSH_CONNECT)
            self.assertEqual(node.tail_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.tail_args.socket_out, SocketType.PUSH_CONNECT)

            node = f._pod_nodes['encoder']
            self.assertEqual(node.head_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.head_args.socket_out, SocketType.ROUTER_BIND)
            for arg in node.peas_args['peas']:
                self.assertEqual(arg.socket_in, SocketType.DEALER_CONNECT)
                self.assertEqual(arg.socket_out, SocketType.PUSH_CONNECT)
            self.assertEqual(node.tail_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.tail_args.socket_out, SocketType.PUSH_CONNECT)

            node = f._pod_nodes['chunk_indexer']
            self.assertEqual(node.head_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.head_args.socket_out, SocketType.PUSH_CONNECT)
            self.assertEqual(node.peas_args['peas'][0].socket_in,
                             node.head_args.socket_in)
            self.assertEqual(node.peas_args['peas'][0].socket_out,
                             node.head_args.socket_out)
            self.assertEqual(node.tail_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.tail_args.socket_out, SocketType.PUSH_CONNECT)

            node = f._pod_nodes['doc_indexer']
            self.assertEqual(node.head_args.socket_in, SocketType.SUB_CONNECT)
            self.assertEqual(node.head_args.socket_out, SocketType.PUSH_CONNECT)
            self.assertEqual(node.peas_args['peas'][0].socket_in,
                             node.head_args.socket_in)
            self.assertEqual(node.peas_args['peas'][0].socket_out,
                             node.head_args.socket_out)
            self.assertEqual(node.tail_args.socket_in, SocketType.SUB_CONNECT)
            self.assertEqual(node.tail_args.socket_out, SocketType.PUSH_CONNECT)

            node = f._pod_nodes['join_all']
            self.assertEqual(node.head_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.head_args.socket_out, SocketType.PUSH_BIND)
            self.assertEqual(node.peas_args['peas'][0].socket_in,
                             node.head_args.socket_in)
            self.assertEqual(node.peas_args['peas'][0].socket_out,
                             node.head_args.socket_out)
            self.assertEqual(node.tail_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.tail_args.socket_out, SocketType.PUSH_BIND)
            f.dry_run()

    def test_query(self):
        f = Flow.load_config(os.path.join(cur_dir, '../yaml/examples/faces/flow-query.yml'))
        with f:
            node = f._pod_nodes['gateway']
            self.assertEqual(node.head_args.socket_in, SocketType.PULL_CONNECT)
            self.assertEqual(node.tail_args.socket_out, SocketType.PUSH_CONNECT)

            node = f._pod_nodes['loader']
            self.assertEqual(node.head_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.head_args.socket_out, SocketType.ROUTER_BIND)
            for arg in node.peas_args['peas']:
                self.assertEqual(arg.socket_in, SocketType.DEALER_CONNECT)
                self.assertEqual(arg.socket_out, SocketType.PUSH_CONNECT)
            self.assertEqual(node.tail_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.tail_args.socket_out, SocketType.PUSH_CONNECT)

            node = f._pod_nodes['flipper']
            self.assertEqual(node.head_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.head_args.socket_out, SocketType.ROUTER_BIND)
            for arg in node.peas_args['peas']:
                self.assertEqual(arg.socket_in, SocketType.DEALER_CONNECT)
                self.assertEqual(arg.socket_out, SocketType.PUSH_CONNECT)
            self.assertEqual(node.tail_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.tail_args.socket_out, SocketType.PUSH_CONNECT)

            node = f._pod_nodes['normalizer']
            self.assertEqual(node.head_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.head_args.socket_out, SocketType.ROUTER_BIND)
            for arg in node.peas_args['peas']:
                self.assertEqual(arg.socket_in, SocketType.DEALER_CONNECT)
                self.assertEqual(arg.socket_out, SocketType.PUSH_CONNECT)
            self.assertEqual(node.tail_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.tail_args.socket_out, SocketType.PUSH_CONNECT)

            node = f._pod_nodes['encoder']
            self.assertEqual(node.head_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.head_args.socket_out, SocketType.ROUTER_BIND)
            for arg in node.peas_args['peas']:
                self.assertEqual(arg.socket_in, SocketType.DEALER_CONNECT)
                self.assertEqual(arg.socket_out, SocketType.PUSH_CONNECT)
            self.assertEqual(node.tail_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.tail_args.socket_out, SocketType.PUSH_CONNECT)

            node = f._pod_nodes['chunk_indexer']
            self.assertEqual(node.head_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.head_args.socket_out, SocketType.PUSH_CONNECT)
            self.assertEqual(node.peas_args['peas'][0].socket_in,
                             node.head_args.socket_in)
            self.assertEqual(node.peas_args['peas'][0].socket_out,
                             node.head_args.socket_out)
            self.assertEqual(node.tail_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.tail_args.socket_out, SocketType.PUSH_CONNECT)

            node = f._pod_nodes['ranker']
            self.assertEqual(node.head_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.head_args.socket_out, SocketType.PUSH_CONNECT)
            self.assertEqual(node.peas_args['peas'][0].socket_in,
                             node.head_args.socket_in)
            self.assertEqual(node.peas_args['peas'][0].socket_out,
                             node.head_args.socket_out)
            self.assertEqual(node.tail_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.tail_args.socket_out, SocketType.PUSH_CONNECT)

            node = f._pod_nodes['doc_indexer']
            self.assertEqual(node.head_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.head_args.socket_out, SocketType.PUSH_BIND)
            self.assertEqual(node.peas_args['peas'][0].socket_in,
                             node.head_args.socket_in)
            self.assertEqual(node.peas_args['peas'][0].socket_out,
                             node.head_args.socket_out)
            self.assertEqual(node.tail_args.socket_in, SocketType.PULL_BIND)
            self.assertEqual(node.tail_args.socket_out, SocketType.PUSH_BIND)
            f.dry_run()


if __name__ == '__main__':
    unittest.main()
