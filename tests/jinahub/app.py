from jina import Flow

if __name__ == '__main__':
    with Flow.load_config('flow.yml') as f:
        f.block()
