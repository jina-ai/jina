import json
import os
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from ..logging.predefined import default_logger


def _get_hubble_url() -> str:
    try:
        req = Request(
            'https://api.jina.ai/hub/hubble.json', headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urlopen(req) as resp:
            return json.load(resp)['url']
    except:
        default_logger.critical('Can not fetch the URL of Hubble from `api.jina.ai`')
        exit(1)


DEFAULT_JINA_HUB_ROOT = Path.home().joinpath('.jina', 'hub-packages')
DEFAULT_JINA_HUB_CACHE_DIR = Path.home().joinpath('.cache', 'jina')
JINA_HUBBLE_REGISTRY = os.environ.get('JINA_HUBBLE_REGISTRY', _get_hubble_url())
JINA_HUBBLE_PUSHPULL_URL = urljoin(JINA_HUBBLE_REGISTRY, '/v1/executors')
JINA_HUB_CACHE_DIR = Path(
    os.environ.get('JINA_HUB_CACHE_DIR', DEFAULT_JINA_HUB_CACHE_DIR)
)
JINA_HUB_CACHE_DIR.mkdir(parents=True, exist_ok=True)
JINA_HUB_ROOT = Path(os.environ.get('JINA_HUB_ROOT', DEFAULT_JINA_HUB_ROOT))
JINA_HUB_ROOT.mkdir(parents=True, exist_ok=True)
