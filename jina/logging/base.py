from .logger import JinaLogger


def get_logger(*args, **kwargs):
    return JinaLogger(*args, **kwargs)
