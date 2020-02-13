from .base import get_logger

profile_logger = get_logger('PROFILE', profiling=True)  #: a logger for profiling
default_logger = get_logger('JINA')  #: a logger at the global-level
