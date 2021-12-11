import warnings
from typing import List, Union, Any, Optional

from ...helper import T, typename, dunder_get


class GetSetAttributeMixin:
    """Provide helper functions for :class:`Document` to allow advanced set and get attributes """

    _special_mapped_keys = ('scores', 'evaluations')

    def __getattr__(self, item):
        if item in self._ON_GETATTR:
            self._increaseVersion()
        if hasattr(self._pb_body, item):
            value = getattr(self._pb_body, item)
        elif '__' in item:
            value = dunder_get(self._pb_body, item)
        else:
            raise AttributeError(f'no attribute named `{item}`')
        return value

    def get_attributes(self, *fields: str) -> Union[Any, List[Any]]:
        """Bulk fetch Document fields and return a list of the values of these fields

        .. note::
            Arguments will be extracted using `dunder_get`
            .. highlight:: python
            .. code-block:: python

                d = Document({'id': '123', 'hello': 'world', 'tags': {'id': 'external_id', 'good': 'bye'}})

                assert d.id == '123'  # true
                assert d.tags['hello'] == 'world' # true
                assert d.tags['good'] == 'bye' # true
                assert d.tags['id'] == 'external_id' # true

                res = d.get_attrs_values(*['id', 'tags__hello', 'tags__good', 'tags__id'])

                assert res == ['123', 'world', 'bye', 'external_id']

        :param fields: the variable length values to extract from the document
        :return: a list with the attributes of this document ordered as the args
        """

        ret = []
        for k in fields:
            try:
                value = getattr(self, k)

                if value is None:
                    raise ValueError

                ret.append(value)
            except (AttributeError, ValueError):
                warnings.warn(
                    f'Could not get attribute `{typename(self)}.{k}`, returning `None`'
                )
                ret.append(None)

        # unboxing if args is single
        if len(fields) == 1:
            ret = ret[0]

        return ret

    def _set_attributes(self, **kwargs) -> None:
        """Bulk update Document fields with key-value specified in kwargs

        .. seealso::
            :meth:`get_attributes` for bulk get attributes

        :param kwargs: the keyword arguments to set the values, where the keys are the fields to set
        """
        for k, v in kwargs.items():
            if isinstance(v, (list, tuple)):
                if k == 'chunks':
                    self.chunks.extend(v)
                elif k == 'matches':
                    self.matches.extend(v)
                elif k == 'embedding':
                    self.embedding = v
                elif k == 'blob':
                    self.blob = v
                else:
                    self._pb_body.ClearField(k)
                    getattr(self._pb_body, k).extend(v)
            elif isinstance(v, dict) and k not in self._special_mapped_keys:
                self._pb_body.ClearField(k)
                getattr(self._pb_body, k).update(v)
            else:
                cls = type(self)
                if (
                    hasattr(cls, k)
                    and isinstance(getattr(cls, k), property)
                    and getattr(cls, k).fset
                ):
                    # if class property has a setter
                    setattr(self, k, v)
                elif hasattr(self._pb_body, k):
                    # no property setter, but proto has this attribute so fallback to proto
                    setattr(self._pb_body, k, v)
                else:
                    raise AttributeError(f'{k} is not recognized')

    def update(
        self: T,
        source: T,
        fields: Optional[List[str]] = None,
    ) -> None:
        """Updates fields specified in ``fields`` from the source to current Document.

        :param source: The :class:`Document` we want to update from as source. The current
            :class:`Document` is referred as destination.
        :param fields: a list of field names that we want to update, if not specified,
            use all present fields in source.

        .. note::
            *. if ``fields`` are empty, then all present fields in source will be merged into current document.
            * `tags` will be updated like a python :attr:`dict`.
            *. the current :class:`Document` will be modified in place, ``source`` will be unchanged.
            *. if current document has more fields than :attr:`source`, these extra fields wll be preserved.
        """
        # We do a safe update: only update existent (value being set) fields from source.
        present_fields = [
            field_descriptor.name
            for field_descriptor, _ in source._pb_body.ListFields()
        ]
        if not fields:
            fields = present_fields  # if `fields` empty, update all present fields.
        for field in fields:
            if (
                field == 'tags'
            ):  # For the tags, stay consistent with the python update method.
                self.tags.update(source.tags)
            else:
                self._pb_body.ClearField(field)
                try:
                    setattr(self, field, getattr(source, field))
                except AttributeError:
                    setattr(self._pb_body, field, getattr(source, field))
