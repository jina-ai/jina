import os
from pathlib import Path

DEFAULT_JINA_HUB_ROOT = Path.home().joinpath(".jina", "hub-packages")
DEFAULT_JINA_HUB_CACHE_DIR = Path.home().joinpath(".cache", "jina")

JINA_HUB_ROOT = Path(os.environ.get("JINA_HUB_ROOT", DEFAULT_JINA_HUB_ROOT))
JINA_HUB_ROOT.mkdir(parents=True, exist_ok=True)

JINA_HUB_CACHE_DIR = Path(
    os.environ.get("JINA_HUB_CACHE_DIR", DEFAULT_JINA_HUB_CACHE_DIR)
)
JINA_HUB_CACHE_DIR.mkdir(parents=True, exist_ok=True)
