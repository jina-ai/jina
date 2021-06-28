import os
from pathlib import Path

JINA_HUB_CACHE_DIR = Path(
    os.environ.get('JINA_HUB_CACHE_DIR', Path.home().joinpath('.cache', 'jina'))
)
JINA_HUB_ROOT = Path(
    os.environ.get('JINA_HUB_ROOT', Path.home().joinpath('.jina', 'hub-packages'))
)
JINA_HUB_CACHE_DIR.mkdir(parents=True, exist_ok=True)
JINA_HUB_ROOT.mkdir(parents=True, exist_ok=True)
