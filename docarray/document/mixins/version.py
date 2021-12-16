import functools


class VersionedMixin:
    """
    Helper class to add versioning to an object. The version number is incremented each time an attribute is set.
    """

    _version = 0
    _ON_GETATTR = ['matches', 'chunks']

    def _increase_version(self):
        super().__setattr__('_version', self._version + 1)

    def __setattr__(self, attr, value):
        super().__setattr__(attr, value)
        self._increase_version()

    def __delattr__(self, attr):
        super(VersionedMixin, self).__delattr__(attr)
        self._increase_version()


def versioned(fn):
    """
    Decorator function that increases the version number each time the decorated method is called.
    The class of the decorated method must be a subclass of :class:`VersionedMixin`
    :param fn: the method to decorate
    :return: decorated function
    """

    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        self._increase_version()
        return fn(self, *args, **kwargs)

    return wrapper
