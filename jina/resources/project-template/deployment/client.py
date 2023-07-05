from jina import Client
from docarray import DocList
from docarray.documents import TextDoc

if __name__ == '__main__':
    c = Client(host='grpc://0.0.0.0:54321')
    da = c.post('/', DocList[TextDoc]([TextDoc(), TextDoc()], return_type=DocList[TextDoc])
    print(da.text)
