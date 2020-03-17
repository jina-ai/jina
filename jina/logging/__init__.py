import os

from .base import get_logger

default_logger = get_logger('JINA')  #: a logger at the global-level

profile_logger = default_logger
if os.environ.get('JINA_PROFILING_LOGGER', False):
    profile_logger = get_logger('PROFILE', log_profile=True)  #: a logger for profiling
