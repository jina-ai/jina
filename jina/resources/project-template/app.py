from docarray import Document
from jina import Flow

f = Flow().add(uses='executor1/config.yml')

with f:
    da = f.post('/', [Document(), Document()])
    print(da.texts)
