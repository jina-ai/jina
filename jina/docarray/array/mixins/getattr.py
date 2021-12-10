from typing import Union, List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ..document import DocumentArray


class GetAttributeMixin:
    """Helpers that provide attributes getter in bulk """

    def get_attributes(self, *fields: str) -> Union[List, List[List]]:
        """Return all nonempty values of the fields from all docs this array contains

        :param fields: Variable length argument with the name of the fields to extract
        :return: Returns a list of the values for these fields.
            When `fields` has multiple values, then it returns a list of list.
        """
        contents = [doc.get_attributes(*fields) for doc in self]

        if len(fields) > 1:
            contents = list(map(list, zip(*contents)))

        return contents

    def get_attributes_with_docs(
        self,
        *fields: str,
    ) -> Tuple[Union[List, List[List]], 'DocumentArray']:
        """Return all nonempty values of the fields together with their nonempty docs

        :param fields: Variable length argument with the name of the fields to extract
        :return: Returns a tuple. The first element is  a list of the values for these fields.
            When `fields` has multiple values, then it returns a list of list. The second element is the non-empty docs.
        """

        contents = []
        docs_pts = []

        for doc in self:
            contents.append(doc.get_attributes(*fields))
            docs_pts.append(doc)

        if len(fields) > 1:
            contents = list(map(list, zip(*contents)))

        from ..document import DocumentArray

        return contents, DocumentArray(docs_pts)
