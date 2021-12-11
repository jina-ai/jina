from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from pandas import DataFrame
    from ....helper import T


class DataframeIOMixin:
    """Save/load from :class:`pandas.dataframe`

    .. note::
        These functions require you to install `pandas`

    """

    def to_dataframe(self, **kwargs) -> 'DataFrame':
        """Export itself to a :class:`pandas.DataFrame` object.

        :param kwargs: the extra kwargs will be passed to :meth:`pandas.DataFrame.from_dict`.
        :return: a :class:`pandas.DataFrame` object
        """
        from pandas import DataFrame

        return DataFrame.from_dict(self.to_list(), **kwargs)

    @classmethod
    def from_dataframe(cls: Type['T'], df: 'DataFrame') -> 'T':
        """Import a :class:`DocumentArray` from a :class:`pandas.DataFrame` object.

        :param df: a :class:`pandas.DataFrame` object.
        :return: a :class:`DocumentArray` object
        """
        da = cls()
        from ....document import Document

        for m in df.to_dict(orient='records'):
            # drop nan
            da.append(
                Document(
                    {k: v for k, v in m.items() if (not isinstance(v, float) or v == v)}
                )
            )
        return da
