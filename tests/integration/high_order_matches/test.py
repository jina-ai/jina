from jina import Executor, Flow, Document, requests


class MyExecutor(Executor):
    @requests(on='/random_work')
    def foo(self, **kwargs):
        print(kwargs)


f = Flow().add(uses=MyExecutor)

with f:
    f.post(on='/random_work', inputs=Document(), on_done=print)
