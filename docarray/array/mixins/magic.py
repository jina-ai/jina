from typing import TYPE_CHECKING

from ...helper import typename

if TYPE_CHECKING:
    from ..types import DocumentArraySourceType


class MagicMixin:
    """Magic helpers for DA/DAM. """

    def __bool__(self):
        """To simulate ```l = []; if l: ...```

        :return: returns true if the length of the array is larger than 0
        """
        return len(self) > 0

    def __repr__(self):
        return f'<{typename(self)} (length={len(self)}) at {id(self)}>'

    def __add__(self, other: 'DocumentArraySourceType'):
        v = type(self)()
        for doc in self:
            v.append(doc)
        for doc in other:
            v.append(doc)
        return v

    def __iadd__(self, other: 'DocumentArraySourceType'):
        for doc in other:
            self.append(doc)
        return self

    def __getstate__(self):
        r = dict(serialized=bytes(self))
        if hasattr(self, '_ref_doc'):
            r['ref_doc'] = bytes(self._ref_doc)
        return r

    def __setstate__(self, state):
        from ..document import DocumentArray

        da = DocumentArray.load_binary(state['serialized'])
        if 'ref_doc' in state:
            from ...document import Document

            ref_doc = Document(state['ref_doc'])
            self.__init__(da, ref_doc)
        else:
            self.__init__()
            self.extend(da)
