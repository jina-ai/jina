"""Decorators and wrappers designed for wrapping :class:`BaseExecutor` functions. """

__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import inspect
from functools import wraps
from typing import Callable, Any, Union, Iterator, List, Optional, Dict

import numpy as np

from .metas import get_default_metas
from ..helper import batch_iterator, typename, convert_tuple_to_list
from ..logging import default_logger
from itertools import islice


def as_aggregate_method(func: Callable) -> Callable:
    """Mark a function so that it keeps track of the number of documents evaluated and a running sum
    to have always access to average value
    """

    @wraps(func)
    def arg_wrapper(self, *args, **kwargs):
        f = func(self, *args, **kwargs)
        self._running_stats += f
        return f

    return arg_wrapper


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
            self.logger.warning(f'"{typename(self)}" has been trained already, '
                                'training it again will override the previous training')
        f = func(self, *args, **kwargs)
        self.is_trained = True
        return f

    return arg_wrapper


def wrap_func(cls, func_lst, wrapper):
    """ Wrapping a class method only once, inherited but not overrided method will not be wrapped again

    :param cls: class
    :param func_lst: function list to wrap
    :param wrapper: the wrapper
    :return:
    """
    for f_name in func_lst:
        if hasattr(cls, f_name) and all(getattr(cls, f_name) != getattr(i, f_name, None) for i in cls.mro()[1:]):
            setattr(cls, f_name, wrapper(getattr(cls, f_name)))


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
        convert_tuple_to_list(self._init_kwargs_dict)
        f = func(self, *args, **kwargs)
        return f

    return arg_wrapper

def _get_slice(data: Union[Iterator[Any], List[Any], np.ndarray], total_size: int) -> Union[Iterator[Any], List[Any], np.ndarray]:
    if isinstance(data, Dict):
        data = islice(data.items(), total_size)
    else:
        data = data[:total_size]
    return data

def _get_size(data: Union[Iterator[Any], List[Any], np.ndarray], axis: int = 0) -> int:
    if isinstance(data, np.ndarray):
        total_size = data.shape[axis]
    elif hasattr(data, '__len__'):
        total_size = len(data)
    else:
        total_size = None
    return total_size


def _get_total_size(full_data_size, batch_size, num_batch):
    batched_data_size = batch_size * num_batch if num_batch else None

    if full_data_size is not None and batched_data_size is not None:
        total_size = min(full_data_size, batched_data_size)
    else:
        total_size = full_data_size or batched_data_size
    return total_size


def _merge_results_after_batching(final_result, merge_over_axis: int = 0):
    if len(final_result) == 1:
        # the only result of one batch
        return final_result[0]

    if len(final_result) and merge_over_axis is not None:
        if isinstance(final_result[0], np.ndarray):
            final_result = np.concatenate(final_result, merge_over_axis)
        elif isinstance(final_result[0], tuple):
            reduced_result = []
            num_cols = len(final_result[0])
            for col in range(num_cols):
                reduced_result.append(np.concatenate([row[col] for row in final_result], merge_over_axis))
            final_result = tuple(reduced_result)

    if len(final_result):
        return final_result


def batching(func: Callable[[Any], np.ndarray] = None,
             batch_size: Union[int, Callable] = None,
             num_batch: Optional[int] = None,
             split_over_axis: int = 0,
             merge_over_axis: int = 0,
             slice_on: int = 1,
             label_on: Optional[int] = None,
             ordinal_idx_arg: Optional[int] = None) -> Any:
    """Split the input of a function into small batches and call :func:`func` on each batch
    , collect the merged result and return. This is useful when the input is too big to fit into memory

    :param func: function to decorate
    :param batch_size: size of each batch
    :param num_batch: number of batches to take, the rest will be ignored
    :param split_over_axis: split over which axis into batches
    :param merge_over_axis: merge over which axis into a single result
    :param slice_on: the location of the data. When using inside a class,
            ``slice_on`` should take ``self`` into consideration.
    :param label_on: the location of the labels. Useful for data with any kind of accompanying labels
    :param ordinal_idx_arg: the location of the ordinal indexes argument. Needed for classes
            where function decorated needs to know the ordinal indexes of the data in the batch
            (Not used when label_on is used)
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
            # by default data is in args[1] (self needs to be taken into account)
            data = args[slice_on]
            args = list(args)

            b_size = (batch_size(data) if callable(batch_size) else batch_size) or getattr(args[0], 'batch_size', None)
            # no batching if b_size is None
            if b_size is None or data is None:
                return func(*args, **kwargs)

            default_logger.debug(
                f'batching enabled for {func.__qualname__} batch_size={b_size} '
                f'num_batch={num_batch} axis={split_over_axis}')

            full_data_size = _get_size(data, split_over_axis)
            total_size = _get_total_size(full_data_size, batch_size, num_batch)

            final_result = []

            data = (data, args[label_on]) if label_on else data

            yield_slice = isinstance(data, np.memmap)
            slice_idx = None

            for b in batch_iterator(data[:total_size], b_size, split_over_axis, yield_slice=yield_slice):
                if yield_slice:
                    slice_idx = b
                    new_memmap = np.memmap(data.filename, dtype=data.dtype, mode='r', shape=data.shape)
                    b = new_memmap[slice_idx]
                    slice_idx = slice_idx[split_over_axis]
                    if slice_idx.start is None or slice_idx.stop is None:
                        slice_idx = None

                if not isinstance(b, tuple):
                    # for now, keeping ordered_idx is only supported if no labels
                    args[slice_on] = b
                    if ordinal_idx_arg and slice_idx is not None:
                        args[ordinal_idx_arg] = slice_idx
                else:
                    args[slice_on] = b[0]
                    args[label_on] = b[1]

                r = func(*args, **kwargs)

                if yield_slice:
                    del new_memmap

                if r is not None:
                    final_result.append(r)

            return _merge_results_after_batching(final_result, merge_over_axis)

        return arg_wrapper

    if func:
        return _batching(func)
    else:
        return _batching


def batching_multi_input(func: Callable[[Any], np.ndarray] = None,
                         batch_size: Union[int, Callable] = None,
                         num_batch: Optional[int] = None,
                         split_over_axis: int = 0,
                         merge_over_axis: int = 0,
                         slice_on: int = 1,
                         num_data: int = 1) -> Any:
    """Split the input of a function into small batches and call :func:`func` on each batch
    , collect the merged result and return. This is useful when the input is too big to fit into memory

    :param func: function to decorate
    :param batch_size: size of each batch
    :param num_batch: number of batches to take, the rest will be ignored
    :param split_over_axis: split over which axis into batches
    :param merge_over_axis: merge over which axis into a single result
    :param slice_on: the location of the data. When using inside a class,
            ``slice_on`` should take ``self`` into consideration.
    :param num_data: the number of data inside the arguments
    :return: the merged result as if run :func:`func` once on the input.

    ..warning:
        data arguments will be taken starting from ``slice_on` to ``slice_on + num_data``

    Example:
        .. highlight:: python
        .. code-block:: python

            class MultiModalExecutor:

                @batching_multi_input(batch_size = 64, num_data=2)
                def encode(self, *batches, **kwargs):
                    batch_modality0 = batches[0]
                    embed0 = _encode_modality(batch_modality0)
                    batch_modality1 = batches[1]
                    embed1 = _encode_modality(batch_modality0)

            class MemoryHungryRanker:

                @batching_multi_input(batch_size = 64, slice_on = 2 , num_data=2)
                def score(
                    self, query_meta: Dict, old_match_scores: Dict, match_meta: Dict
                ) -> 'np.ndarray':
                ...
    """

    def _batching(func):
        @wraps(func)
        def arg_wrapper(*args, **kwargs):
            data = args[slice_on]
            # priority: decorator > class_attribute
            # by default data is in args[1:] (self needs to be taken into account)
            b_size = batch_size or getattr(args[0], 'batch_size', None)
            # no batching if b_size is None
            if b_size is None or data is None:
                return func(*args, **kwargs)

            args = list(args)
            default_logger.debug(
                f'batching enabled for {func.__qualname__} batch_size={b_size} '
                f'num_batch={num_batch} axis={split_over_axis}')

            # assume all datas have the same length
            full_data_size = _get_size(args[slice_on], split_over_axis)
            total_size = _get_total_size(full_data_size, b_size, num_batch)
            final_result = []
            yield_dict = [isinstance(args[slice_on + i], Dict) for i in range(0,num_data)]
            data_iterators = [batch_iterator(_get_slice(args[slice_on + i], total_size), b_size , split_over_axis,
                            yield_dict=yield_dict[i]) for i in range(0, num_data)]

            for batch in data_iterators[0]:
                args[slice_on] = batch
                for idx in range(1, num_data):
                    args[slice_on + idx] = next(data_iterators[idx])

                r = func(*args, **kwargs)

                if r is not None:
                    final_result.append(r)

            return _merge_results_after_batching(final_result, merge_over_axis)

        return arg_wrapper

    if func:
        return _batching(func)
    else:
        return _batching
