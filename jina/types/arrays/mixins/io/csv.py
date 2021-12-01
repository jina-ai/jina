import csv
from contextlib import nullcontext
from typing import Union, TextIO, Optional, Dict, TYPE_CHECKING, Type

if TYPE_CHECKING:
    from .....helper import T


class CsvIOMixin:
    """CSV IO helper.

    can be applied to DA & DAM
    """

    def save_csv(self, file: Union[str, TextIO], flatten_tags: bool = True) -> None:
        """Save array elements into a CSV file.

        :param file: File or filename to which the data is saved.
        :param flatten_tags: if set, then all fields in ``Document.tags`` will be flattened into ``tag__fieldname`` and
            stored as separated columns. It is useful when ``tags`` contain a lot of information.
        """
        if hasattr(file, 'write'):
            file_ctx = nullcontext(file)
        else:
            file_ctx = open(file, 'w')

        with file_ctx as fp:
            if flatten_tags:
                keys = list(self[0].dict().keys()) + list(
                    f'tag__{k}' for k in self[0].tags
                )
                keys.remove('tags')
            else:
                keys = list(self[0].dict().keys())

            writer = csv.DictWriter(fp, fieldnames=keys)

            writer.writeheader()
            for d in self:
                pd = d.dict()
                if flatten_tags:
                    t = pd.pop('tags')
                    pd.update({f'tag__{k}': v for k, v in t.items()})
                writer.writerow(pd)

    @classmethod
    def load_csv(
        cls: Type['T'],
        file: Union[str, TextIO],
        field_resolver: Optional[Dict[str, str]] = None,
    ) -> 'T':
        """Load array elements from a binary file.

        :param file: File or filename to which the data is saved.
        :param field_resolver: a map from field names defined in JSON, dict to the field
            names defined in Document.
        :return: a DocumentArray object
        """

        from ....document.generators import from_csv

        da = cls()
        da.extend(from_csv(file, field_resolver=field_resolver))
        return da
