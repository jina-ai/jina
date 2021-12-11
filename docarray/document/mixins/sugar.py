from typing import overload, TYPE_CHECKING, Union, Callable, Optional, Tuple

if TYPE_CHECKING:
    from ... import DocumentArray, DocumentArrayMemmap
    from ...ndarray import ArrayType
    from ...array.mixins.embed import AnyDNN
    from ...helper import T

    import numpy as np


class SingletonSugarMixin:
    """Provide sugary syntax for :class:`Document` by inheriting methods from :class:`DocumentArray`"""

    @overload
    def match(
        self: 'T',
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
        num_worker: Optional[int] = 1,
    ) -> 'T':
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
        :param batch_size: if provided, then ``darray`` is loaded in batches, where each of them is at most ``batch_size``
            elements. When `darray` is big, this can significantly speedup the computation.
        :param exclude_self: if set, Documents in ``darray`` with same ``id`` as the left-hand values will not be
                        considered as matches.
        :param only_id: if set, then returning matches will only contain ``id``
        :param use_scipy: if set, use ``scipy`` as the computation backend. Note, ``scipy`` does not support distance
            on sparse matrix.
        :param num_worker: the number of parallel workers. If not given, then the number of CPUs in the system will be used.

                .. note::
                    This argument is only effective when ``batch_size`` is set.
        """
        ...

    def match(self: 'T', *args, **kwargs) -> 'T':
        """
        # noqa: D102
        # noqa: DAR101
        :return: itself after modified
        """
        from ... import DocumentArray

        _tmp = DocumentArray([self])
        _tmp.match(*args, **kwargs)
        return self

    @overload
    def embed(
        self: 'T',
        embed_model: 'AnyDNN',
        device: str = 'cpu',
        batch_size: int = 256,
    ) -> 'T':
        """Fill the embedding of Documents inplace by using `embed_model`

        :param embed_model: the embedding model written in Keras/Pytorch/Paddle
        :param device: the computational device for `embed_model`, can be either
            `cpu` or `cuda`.
        :param batch_size: number of Documents in a batch for embedding
        """

    def embed(self: 'T', *args, **kwargs) -> 'T':
        """
        # noqa: D102
        # noqa: DAR101
        :return: itself after modified.
        """
        from ... import DocumentArray

        _tmp = DocumentArray([self])
        _tmp.embed(*args, **kwargs)
        return self
