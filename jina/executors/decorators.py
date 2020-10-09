__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from ..logging import default_logger

"""Decorators and wrappers designed for wrapping :class:`BaseExecutor` functions. """

import inspect
from functools import wraps
from typing import Callable, Any, Union, Iterator, List

import numpy as np

from .metas import get_default_metas
from ..helper import batch_iterator


def as_update_method(func: Callable) -> Callable:
    """Mark the function as the updating function of this executor,
    calling this function will change the executor so later you can save the change via :func:`save`
    Will set the is_updated property after function is called.
    """

    @wraps(func)
    def arg_wrapper(self, *args, **kwargs):
        f = func(self, *args, **kwargs)
        self.is_updated = True
        return f

    return arg_wrapper


def as_train_method(func: Callable) -> Callable:
    """Mark a function as the training function of this executor.
    Will set the is_trained property after function is called.
    """

    @wraps(func)
    def arg_wrapper(self, *args, **kwargs):
        if self.is_trained:
            self.logger.warning('"%s" has been trained already, '
                                'training it again will override the previous training' % self.__class__.__name__)
        f = func(self, *args, **kwargs)
        self.is_trained = True
        return f

    return arg_wrapper


def as_ndarray(func: Callable, dtype=np.float32) -> Callable:
    """Convert an :class:`BaseExecutor` function returns to a ``numpy.ndarray``,
    the following type are supported: `EagerTensor`, `Tensor`, `list`

    :param func: the function to decorate
    :param dtype: the converted dtype of the ``numpy.ndarray``
    """

    @wraps(func)
    def arg_wrapper(self, *args, **kwargs):
        r = func(self, *args, **kwargs)
        r_type = type(r).__name__
        if r_type in {'ndarray', 'EagerTensor', 'Tensor', 'list'}:
            return np.array(r, dtype)
        else:
            raise TypeError(f'unrecognized type {r_type}: {type(r)}')

    return arg_wrapper


def require_train(func: Callable) -> Callable:
    """Mark an :class:`BaseExecutor` function as training required, so it can only be called
    after the function decorated by ``@as_train_method``. """

    @wraps(func)
    def arg_wrapper(self, *args, **kwargs):
        if hasattr(self, 'is_trained'):
            if self.is_trained:
                return func(self, *args, **kwargs)
            else:
                raise RuntimeError(f'training is required before calling "{func.__name__}"')
        else:
            raise AttributeError(f'{self!r} has no attribute "is_trained"')

    return arg_wrapper


def store_init_kwargs(func: Callable) -> Callable:
    """Mark the args and kwargs of :func:`__init__` later to be stored via :func:`save_config` in YAML """

    @wraps(func)
    def arg_wrapper(self, *args, **kwargs):
        if func.__name__ != '__init__':
            raise TypeError('this decorator should only be used on __init__ method of an executor')
        taboo = {'self', 'args', 'kwargs'}
        _defaults = get_default_metas()
        taboo.update(_defaults.keys())
        all_pars = inspect.signature(func).parameters
        tmp = {k: v.default for k, v in all_pars.items() if k not in taboo}
        tmp_list = [k for k in all_pars.keys() if k not in taboo]
        # set args by aligning tmp_list with arg values
        for k, v in zip(tmp_list, args):
            tmp[k] = v
        # set kwargs
        for k, v in kwargs.items():
            if k in tmp:
                tmp[k] = v

        if getattr(self, 'store_args_kwargs', None):
            if args: tmp['args'] = args
            if kwargs: tmp['kwargs'] = {k: v for k, v in kwargs.items() if k not in taboo}

        if hasattr(self, '_init_kwargs_dict'):
            self._init_kwargs_dict.update(tmp)
        else:
            self._init_kwargs_dict = tmp
        f = func(self, *args, **kwargs)
        return f

    return arg_wrapper


def batching(func: Callable[[Any], np.ndarray] = None, *,
             batch_size: Union[int, Callable] = None, num_batch: int = None,
             split_over_axis: int = 0, merge_over_axis: int = 0, slice_on: int = 1) -> Any:
    """Split the input of a function into small batches and call :func:`func` on each batch
    , collect the merged result and return. This is useful when the input is too big to fit into memory

    :param func: function to decorate
    :param batch_size: size of each batch
    :param num_batch: number of batches to take, the rest will be ignored
    :param split_over_axis: split over which axis into batches
    :param merge_over_axis: merge over which axis into a single result
    :param slice_on: the location of the data. When using inside a class,
            ``slice_on`` should take ``self`` into consideration.
    :return: the merged result as if run :func:`func` once on the input.

    Example:
        .. highlight:: python
        .. code-block:: python

            class MemoryHungryExecutor:

                @batching
                def train(self, batch: 'numpy.ndarray', *args, **kwargs):
                    gpu_train(batch)  #: this will respect the ``batch_size`` defined as object attribute

                @batching(batch_size = 64)
                def train(self, batch: 'numpy.ndarray', *args, **kwargs):
                    gpu_train(batch)


    """

    def _batching(func):
        @wraps(func)
        def arg_wrapper(*args, **kwargs):
            # priority: decorator > class_attribute
            # by default data is in args[0]
            data = args[slice_on]
            args = list(args)

            label = kwargs.get('label', None)

            b_size = (batch_size(data) if callable(batch_size) else batch_size) or getattr(args[0], 'batch_size', None)
            # no batching if b_size is None
            if b_size is None:
                return func(*args, **kwargs)

            default_logger.info(
                f'batching enabled for {func.__qualname__} batch_size={b_size} '
                f'num_batch={num_batch} axis={split_over_axis}')

            total_size1 = _get_size(data, split_over_axis)
            total_size2 = b_size * num_batch if num_batch else None

            if total_size1 is not None and total_size2 is not None:
                total_size = min(total_size1, total_size2)
            else:
                total_size = total_size1 or total_size2

            final_result = []

            if label is not None:
                data = (data, label)

            yield_slice = isinstance(data, np.memmap)

            for b in batch_iterator(data[:total_size], b_size, split_over_axis, yield_slice=yield_slice):
                if yield_slice:
                    new_memmap = np.memmap(data.filename, dtype=data.dtype, mode='r', shape=data.shape)
                    b = new_memmap[b]

                if label is None:
                    args[slice_on] = b
                    r = func(*args, **kwargs)
                else:
                    args[slice_on] = b
                    kwargs['label'] = b[1]
                    r = func(*args, **kwargs)

                if yield_slice:
                    del new_memmap

                if r is not None:
                    final_result.append(r)

            if len(final_result) == 1:
                # the only result of one batch
                return final_result[0]

            if len(final_result) and merge_over_axis is not None:
                if isinstance(final_result[0], np.ndarray):
                    final_result = np.concatenate(final_result, merge_over_axis)
                    # if chunk_dim != -1:
                    #     final_result = final_result.reshape((-1, chunk_dim, final_result.shape[1]))
                elif isinstance(final_result[0], tuple):
                    reduced_result = []
                    num_cols = len(final_result[0])
                    for col in range(num_cols):
                        reduced_result.append(np.concatenate([row[col] for row in final_result], merge_over_axis))
                    # if chunk_dim != -1:
                    #     for col in range(num_cols):
                    #         reduced_result[col] = reduced_result[col].reshape(
                    #             (-1, chunk_dim, reduced_result[col].shape[1]))
                    final_result = tuple(reduced_result)

            if len(final_result):
                return final_result

        return arg_wrapper

    if func:
        return _batching(func)
    else:
        return _batching


def _get_size(data: Union[Iterator[Any], List[Any], np.ndarray], axis: int = 0) -> int:
    if isinstance(data, np.ndarray):
        total_size = data.shape[axis]
    elif hasattr(data, '__len__'):
        total_size = len(data)
    else:
        total_size = None
    return total_size
