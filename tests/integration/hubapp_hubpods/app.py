__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from jina.flow import Flow

if __name__ == '__main__':
    with Flow.load_config('flow.yml') as f:
        f.block()
