import click
import sys
import time
from functools import partial

from jina import Client, Document

from jina.types.request import Response


def pong(peer_hash, resp: Response):
    for d in resp.docs:
        if d.text != peer_hash:
            print(f'⚠️  mismatch: {peer_hash} vs {d.text}')
    sys.stdout.write('#')
    sys.stdout.flush()


def peer_client(port, protocal, peer_hash):
    c = Client(protocol=protocal, port_expose=port)
    while True:
        c.post('/ping', Document(text=peer_hash), on_done=lambda x: pong(peer_hash, x))
        time.sleep(0.5)


@click.command()
@click.argument('port', default=60896)
@click.option('--concurrent', default=10)
@click.option('--protocal', default='http')
def cli(port, protocal, concurrent):
    import threading

    pool = []
    print(f'=> start the {concurrent} peer clients accesing :{port} ...')
    for peer_id in range(concurrent):
        t = threading.Thread(
            target=partial(peer_client, port, protocal, str(peer_id)), daemon=True
        )
        t.start()
        pool.append(t)

    for t in pool:
        t.join()


if __name__ == '__main__':
    cli()
