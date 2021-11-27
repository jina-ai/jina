from typing import overload, TYPE_CHECKING, Union, Callable, Optional, Tuple


if TYPE_CHECKING:
    from ...arrays import DocumentArray
    from ...arrays.memmap import DocumentArrayMemmap
    from ...ndarray import ArrayType
    from ...arrays.mixins.embed import AnyDNN

    import numpy as np


class SingletonSugarMixin:
    """Provide sugary syntax for :class:`Document` by inheriting methods from :class:`DocumentArray`"""

    @overload
    def match(
        self,
        darray: Union['DocumentArray', 'DocumentArrayMemmap'],
        metric: Union[
            str, Callable[['ArrayType', 'ArrayType'], 'np.ndarray']
        ] = 'cosine',
        limit: Optional[Union[int, float]] = 20,
        normalization: Optional[Tuple[float, float]] = None,
        metric_name: Optional[str] = None,
        batch_size: Optional[int] = None,
        exclude_self: bool = False,
        only_id: bool = False,
        use_scipy: bool = False,
    ) -> None:
        """Matching the current Document against a set of Documents.

        The result will be stored in :attr:`.matches`.

        .. note::
            When you want to match a set Documents (let's call it set `A`) against another set of Documents (set `B`),
            where you want to find for each element in `A` what are its nearest neighbours in `B`.
            Then you need :meth:`DocumentArray.match`

        :param darray: the other DocumentArray or DocumentArrayMemmap to match against
        :param metric: the distance metric
        :param limit: the maximum number of matches, when not given defaults to 20.
        :param normalization: a tuple [a, b] to be used with min-max normalization,
                                the min distance will be rescaled to `a`, the max distance will be rescaled to `b`
                                all values will be rescaled into range `[a, b]`.
        :param metric_name: if provided, then match result will be marked with this string.
        :param batch_size: if provided, then `darray` is loaded in chunks of, at most, batch_size elements. This option
                           will be slower but more memory efficient. Specialy indicated if `darray` is a big
                           DocumentArrayMemmap.
        :param exclude_self: if set, Documents in ``darray`` with same ``id`` as the left-hand values will not be
                        considered as matches.
        :param only_id: if set, then returning matches will only contain ``id``
        :param use_scipy: if set, use ``scipy`` as the computation backend. Note, ``scipy`` does not support distance
            on sparse matrix.
        """
        ...

    def match(self, *args, **kwargs) -> None:
        """
        # noqa: D102
        # noqa: DAR101
        """
        from ...arrays import DocumentArray

        _tmp = DocumentArray([self])
        _tmp.match(*args, **kwargs)

    @overload
    def embed(
        self,
        embed_model: 'AnyDNN',
        device: str = 'cpu',
        batch_size: int = 256,
    ) -> None:
        """Fill the embedding of Documents inplace by using `embed_model`

        :param embed_model: the embedding model written in Keras/Pytorch/Paddle
        :param device: the computational device for `embed_model`, can be either
            `cpu` or `cuda`.
        :param batch_size: number of Documents in a batch for embedding
        """

    def embed(self, *args, **kwargs) -> None:
        """
        # noqa: D102
        # noqa: DAR101
        """
        from ...arrays import DocumentArray

        _tmp = DocumentArray([self])
        _tmp.embed(*args, **kwargs)
