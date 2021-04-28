from typing import Optional

from . import DocsExtractUpdateMixin, FlatRecursiveMixin, BaseExecutableDriver


class GenericExecutorDriver(
    DocsExtractUpdateMixin, FlatRecursiveMixin, BaseExecutableDriver
):
    """Generic driver that uses extract-apply-update pattern. It automatically binds to the method
    decorated with `@request`."""

    def __init__(
        self, executor: Optional[str] = None, method: str = '', *args, **kwargs
    ):
        super().__init__(executor, method, *args, **kwargs)
