import os
from .logger import JinaLogger, ProfileLogger, NTLogger
from ..enums import LogVerbosity


def get_logger(context: str, log_profile: bool = False, *args, **kwargs):
    if log_profile:
        return ProfileLogger(context, *args, **kwargs)
    elif os.name == 'nt':  # for Windows
        verbose_level = LogVerbosity.from_string(os.environ.get('JINA_LOG_VERBOSITY', 'INFO'))
        return NTLogger(context, verbose_level)
    else:
        return JinaLogger(context, *args, **kwargs)
