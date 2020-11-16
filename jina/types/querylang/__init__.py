from ...proto import jina_pb2

_empty_querylang = jina_pb2.QueryLangProto()


class QueryLang:
    def __init__(self, name: str, priority: int = 1, **kwargs):
        self._querylang = jina_pb2.QueryLangProto()
        self._querylang.name = name
        self._querylang.priority = priority
        self._querylang.parameters.update(kwargs)

    def __getattr__(self, name: str):
        if hasattr(_empty_querylang, name):
            return getattr(self._document, name)
        else:
            raise AttributeError

    @property
    def as_pb_object(self) -> 'jina_pb2.QueryLangProto':
        return self._querylang

    def disable(self):
        self._querylang.disabled = True
