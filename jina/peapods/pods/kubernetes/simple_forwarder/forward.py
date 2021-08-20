
# Match merger executor

from jina import Executor, requests


class SimpleForwarder(Executor):

    @requests
    def forward(self, docs, parameters, **kwargs):
        try:
            routing_table = self.runtime_args.routing_table
            print(routing_table)
        except AttributeError:
            print('Routing table not found')
        return docs

