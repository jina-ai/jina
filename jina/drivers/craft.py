__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Optional

from . import FlatRecursiveMixin, BaseExecutableDriver

if False:
    from .. import DocumentSet


class CraftDriver(FlatRecursiveMixin, BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`craft` by default """

    def __init__(
        self, executor: Optional[str] = None, method: str = 'craft', *args, **kwargs
    ):
        super().__init__(executor, method, *args, **kwargs)

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs):
        if docs:
            contents, docs_pts = docs.extract_docs(*self.exec.required_keys)

            if docs_pts:
                if len(self.exec.required_keys) > 1:
                    craft_dicts = self.exec_fn(*contents)
                else:
                    craft_dicts = self.exec_fn(contents)

                if len(docs_pts) != len(craft_dicts):
                    self.logger.error(
                        f'mismatched {len(docs_pts)} docs from level {docs_pts[0].granularity} '
                        f'and length of returned crafted documents: {len(craft_dicts)}, the length must be the same'
                    )
                for doc, crafted in zip(docs_pts, craft_dicts):
                    doc.set_attrs(**crafted)
