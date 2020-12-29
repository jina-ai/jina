import os

from jina.enums import SocketType
from jina.flow import Flow

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_index():
    f = Flow.load_config(os.path.join(cur_dir, '../yaml/examples/faiss/flow-index.yml'))
    with f:
        node = f._pod_nodes['gateway']
        assert node.head_args.socket_in == SocketType.PULL_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['crafter']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.head_args.socket_out == SocketType.ROUTER_BIND
        for arg in node.peas_args['peas']:
            assert arg.socket_in == SocketType.DEALER_CONNECT
            assert arg.socket_out == SocketType.PUSH_CONNECT
        assert node.tail_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUB_BIND

        node = f._pod_nodes['encoder']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.head_args.socket_out == SocketType.ROUTER_BIND
        for arg in node.peas_args['peas']:
            assert arg.socket_in == SocketType.DEALER_CONNECT
            assert arg.socket_out == SocketType.PUSH_CONNECT
        assert node.tail_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['faiss_indexer']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.head_args.socket_out == SocketType.PUSH_CONNECT
        assert node.peas_args['peas'][0].socket_in == node.head_args.socket_in
        assert node.peas_args['peas'][0].socket_out == node.head_args.socket_out
        assert node.tail_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['doc_indexer']
        assert node.head_args.socket_in == SocketType.SUB_CONNECT
        assert node.head_args.socket_out == SocketType.PUSH_CONNECT
        assert node.peas_args['peas'][0].socket_in == node.head_args.socket_in
        assert node.peas_args['peas'][0].socket_out == node.head_args.socket_out
        assert node.tail_args.socket_in == SocketType.SUB_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['join_all']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.head_args.socket_out == SocketType.PUSH_BIND
        assert node.peas_args['peas'][0].socket_in == node.head_args.socket_in
        assert node.peas_args['peas'][0].socket_out == node.head_args.socket_out
        assert node.tail_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_BIND



def test_query():
    f = Flow.load_config(os.path.join(cur_dir, '../yaml/examples/faiss/flow-query.yml'))
    with f:
        node = f._pod_nodes['gateway']
        assert node.head_args.socket_in == SocketType.PULL_CONNECT
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['crafter']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.head_args.socket_out == SocketType.ROUTER_BIND
        for arg in node.peas_args['peas']:
            assert arg.socket_in == SocketType.DEALER_CONNECT
            assert arg.socket_out == SocketType.PUSH_CONNECT
        assert node.tail_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['encoder']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.head_args.socket_out == SocketType.ROUTER_BIND
        for arg in node.peas_args['peas']:
            assert arg.socket_in == SocketType.DEALER_CONNECT
            assert arg.socket_out == SocketType.PUSH_CONNECT
        assert node.tail_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['faiss_indexer']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.head_args.socket_out == SocketType.PUSH_CONNECT
        assert node.peas_args['peas'][0].socket_in == node.head_args.socket_in
        assert node.peas_args['peas'][0].socket_out == node.head_args.socket_out
        assert node.tail_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['ranker']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.head_args.socket_out == SocketType.PUSH_CONNECT
        assert node.peas_args['peas'][0].socket_in == node.head_args.socket_in
        assert node.peas_args['peas'][0].socket_out == node.head_args.socket_out
        assert node.tail_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_CONNECT

        node = f._pod_nodes['doc_indexer']
        assert node.head_args.socket_in == SocketType.PULL_BIND
        assert node.head_args.socket_out == SocketType.PUSH_BIND
        assert node.peas_args['peas'][0].socket_in == node.head_args.socket_in
        assert node.peas_args['peas'][0].socket_out == node.head_args.socket_out
        assert node.tail_args.socket_in == SocketType.PULL_BIND
        assert node.tail_args.socket_out == SocketType.PUSH_BIND

