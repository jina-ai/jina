from jina import Flow, Document

f = Flow.load_config('flow-index.yml')

with f:
    f.post(
        on='/index',
        on_done=print,
        inputs=Document(tags={'caption': 'hello', 'image': 'image_1.jpg'}),
    )
