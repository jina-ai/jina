from ..sets import DocumentSet


class DocsPropertyMixin:
    @property
    def docs(self) -> 'DocumentSet':
        self.is_used = True
        return DocumentSet(self.body.docs)


class GroundtruthPropertyMixin:
    @property
    def groundtruths(self) -> 'DocumentSet':
        self.is_used = True
        return DocumentSet(self.body.groundtruths)
