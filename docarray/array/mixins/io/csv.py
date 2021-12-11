import csv
from contextlib import nullcontext
from typing import Union, TextIO, Optional, Dict, TYPE_CHECKING, Type, Sequence

import numpy as np

if TYPE_CHECKING:
    from ....helper import T


class CsvIOMixin:
    """CSV IO helper.

    can be applied to DA & DAM
    """

    def save_embeddings_csv(self, file: Union[str, TextIO], **kwargs) -> None:
        """Save embeddings to a CSV file

        This function utilizes :meth:`numpy.savetxt` internal.

        :param file: File or filename to which the data is saved.
        :param kwargs: extra kwargs will be passed to :meth:`numpy.savetxt`.
        """
        if hasattr(file, 'write'):
            file_ctx = nullcontext(file)
        else:
            file_ctx = open(file, 'w')
        np.savetxt(file_ctx, self.embeddings, **kwargs)

    def save_csv(
        self,
        file: Union[str, TextIO],
        flatten_tags: bool = True,
        exclude_fields: Optional[Sequence[str]] = None,
        dialect: Union[str, 'csv.Dialect'] = 'excel',
    ) -> None:
        """Save array elements into a CSV file.

        :param file: File or filename to which the data is saved.
        :param flatten_tags: if set, then all fields in ``Document.tags`` will be flattened into ``tag__fieldname`` and
            stored as separated columns. It is useful when ``tags`` contain a lot of information.
        :param exclude_fields: if set, those fields wont show up in the output CSV
        :param dialect: define a set of parameters specific to a particular CSV dialect. could be a string that represents
            predefined dialects in your system, or could be a :class:`csv.Dialect` class that groups specific formatting
            parameters together.
        """
        if hasattr(file, 'write'):
            file_ctx = nullcontext(file)
        else:
            file_ctx = open(file, 'w')

        with file_ctx as fp:
            if flatten_tags and self[0].tags:
                keys = list(self[0].to_dict().keys()) + list(
                    f'tag__{k}' for k in self[0].tags
                )
                keys.remove('tags')
            else:
                flatten_tags = False
                keys = list(self[0].to_dict().keys())

            if exclude_fields:
                for k in exclude_fields:
                    if k in keys:
                        keys.remove(k)

            writer = csv.DictWriter(fp, fieldnames=keys, dialect=dialect)

            writer.writeheader()
            from jina import Document

            for d in self:
                _d = d
                if exclude_fields:
                    _d = Document(d, copy=True)
                    _d.pop(*exclude_fields)

                pd = _d.to_dict()
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
