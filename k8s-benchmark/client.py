# from jina import Document
# from jina.clients.grpc import GRPCClient
#
#
# client = GRPCClient(port=8080)
#
# for j in range(10):
#     resp = client.index(inputs=[Document(text=f'test{i}') for i in range(10)], return_results=True)
#     print(resp)


import time

from jina.clients.grpc import GRPCClient

from jina import DocumentArray, Document

REQUEST_CONTENT_LENGTH = 10000

content = 's' * REQUEST_CONTENT_LENGTH
da = DocumentArray([Document(content=content)])

client = GRPCClient(port=8080)

request_count = 100
index_count = 10
for i in range(index_count):
    result = client.index(da)

start_time = time.time()
for i in range(request_count):
    result = client.search(da)
end_time = time.time()

print(end_time - start_time)
