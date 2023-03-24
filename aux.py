import os

os.environ['JINA_LOG_LEVEL'] = 'DEBUG'
import os

from jina import Deployment, Executor, requests, Flow, Client, DocumentArray, Document


# f = Flow(protocol='http', port_expose=8081, expose_graphql_endpoint=True).add()
# with f:
#     f.post(on='/', inputs=DocumentArray([]))
#     time.sleep(5)

class MyExec(Executor):

    @requests(on='/foo')
    async def foo(self, docs, **kwargs):
        print(f' HEY foo {os.getpid()} => {[doc.text for doc in docs]}')
        for doc in docs:
            doc.text += f'return foo {os.getpid()}'

    @requests(on='/bar')
    async def bar(self, docs, **kwargs):
        print(f' HEY bar {os.getpid()} => {[doc.text for doc in docs]}')
        for doc in docs:
            doc.text += f'return bar {os.getpid()}'


# d = Deployment(include_gateway=False, protocol='http', uses=MyExec, port=8081)
# with d:
#     #d.block()
#     c = Client(port=8081, protocol='http')
#     r = c.post(on='/bar', inputs=DocumentArray([Document(text='input ')]))
#     print(f' result {r[0].text}')
#     r = c.post(on='/foo', inputs=DocumentArray([Document(text='input ')]))
#     print(f' result {r[0].text}')
#
# d = Deployment(include_gateway=True, protocol='http', uses=MyExec, port=8081, replicas=2)
# with d:
#     c = Client(port=8081, protocol='http')
#     r = c.post(on='/bar', inputs=DocumentArray([Document(text='input ')]))
#     print(f' result {r[0].text}')
#     r = c.post(on='/foo', inputs=DocumentArray([Document(text='input ')]))
#     print(f' result {r[0].text}')

#
# d = Deployment(include_gateway=False, protocol=['http', 'grpc'], uses=MyExec, ports=[8081, 8082])
# with d:
#     c = Client(port=8081, protocol='http')
#     r = c.post(on='/bar', inputs=DocumentArray([Document(text='input ')]))
#     print(f' result {r[0].text}')
#     r = c.post(on='/foo', inputs=DocumentArray([Document(text='input ')]))
#     print(f' result {r[0].text}')
#     c = Client(port=8082, protocol='grpc')
#     r = c.post(on='/bar', inputs=DocumentArray([Document(text='input ')]))
#     print(f' result {r[0].text}')
#     r = c.post(on='/foo', inputs=DocumentArray([Document(text='input ')]))
#     print(f' result {r[0].text}')
#     d.block()
# #
# # d = Deployment(include_gateway=False, protocol=['grpc', 'http'], uses=MyExec, ports=[8082, 8081])
# # with d:
# #     d.block()
#
#
# d = Deployment(include_gateway=True, protocol='http', uses=MyExec, port=8081, replicas=2)
# with d:
#     d.block()

# d = Deployment(include_gateway=True, protocol='grpc', uses=MyExec, port=8082, replicas=2)
# with d:
#     # c = Client(port=8081, protocol='http')
#     # r = c.post(on='/bar', inputs=DocumentArray([Document(text='input ')]))
#     # print(f' result {r[0].text}')
#     # r = c.post(on='/foo', inputs=DocumentArray([Document(text='input ')]))
#     # print(f' result {r[0].text}')
#     c = Client(port=8082, protocol='grpc')
#     r = c.post(on='/bar', inputs=DocumentArray([Document(text='input ')]))
#     print(f' result {r[0].text}')
#     r = c.post(on='/foo', inputs=DocumentArray([Document(text='input ')]))
#     print(f' result {r[0].text}')
#     d.block()

# d = Deployment(include_gateway=False, protocol='http', uses=MyExec, port=8081)
# with d:
#     #d.block()
#     c = Client(port=8081, protocol='http')
#     r = c.post(on='/bar', inputs=DocumentArray([Document(text='input ')]))
#     print(f' result {r[0].text}')
#     r = c.post(on='/foo', inputs=DocumentArray([Document(text='input ')]))
#     print(f' result {r[0].text}')

# d = Deployment(include_gateway=True, protocol=['http', 'grpc'], uses=MyExec, port=[8081, 8082], replicas=2)
# with d:
#     try:
#         c = Client(port=8082)
#         r = c.post(on='/bar', inputs=DocumentArray([Document(text='input ')]))
#         print(f' result {r[0].text}')
#         r = c.post(on='/foo', inputs=DocumentArray([Document(text='input ')]))
#         print(f' result {r[0].text}')
#         c = Client(port=8081, protocol='http')
#         r = c.post(on='/bar', inputs=DocumentArray([Document(text='input ')]))
#         print(f' result {r[0].text}')
#         r = c.post(on='/foo', inputs=DocumentArray([Document(text='input ')]))
#         print(f' result {r[0].text}')
#     except:
#         pass

d = Deployment(include_gateway=True, protocol=['http', 'grpc'], uses=MyExec, port=[8081, 8082], replicas=2)
with d:
    try:
        c = Client(port=8082)
        r = c.post(on='/bar', inputs=DocumentArray([Document(text='input ')]))
        print(f' result {r[0].text}')
        r = c.post(on='/foo', inputs=DocumentArray([Document(text='input ')]))
        print(f' result {r[0].text}')
        c = Client(port=8081, protocol='http')
        r = c.post(on='/bar', inputs=DocumentArray([Document(text='input ')]))
        print(f' result {r[0].text}')
        r = c.post(on='/foo', inputs=DocumentArray([Document(text='input ')]))
        print(f' result {r[0].text}')
    except:
        pass

# f = Flow(protocol='HTTP', port=8081).add(uses=MyExec)
# with f:
#    f.block()

#
#
#
# f = Flow(protocol='http', port_expose=8081, expose_graphql_endpoint=True).add()
# with f:
#     f.post(on='/', inputs=DocumentArray([]))
#
#
# for replicas in [1, 3]:
#     for shards in [1, 3]:
#         d = Deployment(include_gateway=True, replicas=replicas, shards=shards)
#
#         with d:
#             d.post(on='/', inputs=DocumentArray([]))
#
#
# d = Deployment(include_gateway=False)
#
# with d:
#     d.post(on='/', inputs=DocumentArray([]))
#
#
# for replicas in [1, 3]:
#     d = Deployment(include_gateway=True, replicas=replicas)
#
#     with d:
#         d.post(on='/', inputs=DocumentArray([]))
#
# for replicas in [1, 3]:
#     for shards in [1, 3]:
#         for protocol in ['grpc', 'http', 'websocket']:
#             print(f' ################### replicas {replicas}, shards {shards}, protocol {protocol}')
#             f = Flow(protocol=protocol).add(replicas=replicas, shards=shards)
#
#             with f:
#                 f.post(on='/', inputs=DocumentArray([]))
#
# for replicas in [1, 3]:
#     for shards in [1, 3]:
#         d = Deployment(include_gateway=True, replicas=replicas, shards=shards)
#
#         with d:
#             d.post(on='/', inputs=DocumentArray([]))
