import time
import random
import sys
import click
from jina import Flow, Executor, DocumentArray, requests


class MyExecutor(Executor):
    @requests(on='/ping')
    def ping(self, docs: DocumentArray, **kwargs):
        time.sleep(3 * random.random())


@click.command()
@click.argument('port', default=60896)
@click.option('--polling', default='ANY')
@click.option('--parallel', default=15)
@click.option('--protocal', default='http')
def cli(port, protocal, parallel, polling):
    f = Flow(protocol=protocal, port_expose=port).add(
        uses=MyExecutor, parallel=parallel, polling=polling
    )
    with f:
        f.block()


if __name__ == '__main__':
    cli()
