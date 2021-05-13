from jina import Flow, Document

f = Flow.load_config('flow-index.yml')

inputs = [
    Document(tags={'caption': 'hello', 'image': 'image_1.jpg'}),
    Document(tags={'caption': 'world', 'image': 'image_2.jpg'}),
]

with f:
    f.post(
        on='/index',
        # on_done=print,
        inputs=inputs,
    )
