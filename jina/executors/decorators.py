"""Decorators and wrappers designed for wrapping :class:`BaseExecutor` functions. """

__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import inspect
from functools import wraps
from itertools import islice, chain
from typing import Callable, Any, Union, Iterator, List, Optional, Dict, Iterable
import copy

import numpy as np

from .metas import get_default_metas
from ..helper import batch_iterator, typename, convert_tuple_to_list
from ..logging import default_logger


def as_aggregate_method(func: Callable) -> Callable:
    """Mark a function so that it keeps track of the number of documents evaluated and a running sum
    to have always access to average value
    :param func: the function to decorate
    :return: the wrapped function
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
    :param func: the function to decorate
    :return: the wrapped function
    """

    @wraps(func)
    def arg_wrapper(self, *args, **kwargs):
        f = func(self, *args, **kwargs)
        self.is_updated = True
        return f

    return arg_wrapper


def wrap_func(cls, func_lst, wrapper):
    """Wrapping a class method only once, inherited but not overridden method will not be wrapped again

    :param cls: class
    :param func_lst: function list to wrap
    :param wrapper: the wrapper
    """
    for f_name in func_lst:
        if hasattr(cls, f_name) and all(
            getattr(cls, f_name) != getattr(i, f_name, None) for i in cls.mro()[1:]
        ):
            setattr(cls, f_name, wrapper(getattr(cls, f_name)))


def as_ndarray(func: Callable, dtype=np.float32) -> Callable:
    """Convert an :class:`BaseExecutor` function returns to a ``numpy.ndarray``,
    the following type are supported: `EagerTensor`, `Tensor`, `list`

    :param func: the function to decorate
    :param dtype: the converted dtype of the ``numpy.ndarray``
    :return: the wrapped function
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


def store_init_kwargs(func: Callable) -> Callable:
    """Mark the args and kwargs of :func:`__init__` later to be stored via :func:`save_config` in YAML
    :param func: the function to decorate
    :return: the wrapped function
    """

    @wraps(func)
    def arg_wrapper(self, *args, **kwargs):
        if func.__name__ != '__init__':
            raise TypeError(
                'this decorator should only be used on __init__ method of an executor'
            )
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
            if args:
                tmp['args'] = args
            if kwargs:
                tmp['kwargs'] = {k: v for k, v in kwargs.items() if k not in taboo}

        if hasattr(self, '_init_kwargs_dict'):
            self._init_kwargs_dict.update(tmp)
        else:
            self._init_kwargs_dict = tmp
        convert_tuple_to_list(self._init_kwargs_dict)
        f = func(self, *args, **kwargs)
        return f

    return arg_wrapper


def _get_slice(
    data: Union[Iterator[Any], List[Any], np.ndarray], total_size: int
) -> Union[Iterator[Any], List[Any], np.ndarray]:
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


def _merge_results_after_batching(
    final_result, merge_over_axis: int = 0, flatten: bool = True
):
    if not final_result:
        return

    if isinstance(final_result[0], np.ndarray):
        if len(final_result[0].shape) > 1:
            final_result = np.concatenate(final_result, merge_over_axis)
    elif isinstance(final_result[0], list) and flatten:
        final_result = list(chain.from_iterable(final_result))

    return final_result


def batching(
    func: Optional[Callable[[Any], np.ndarray]] = None,
    batch_size: Optional[Union[int, Callable]] = None,
    num_batch: Optional[int] = None,
    split_over_axis: int = 0,
    merge_over_axis: int = 0,
    slice_on: int = 1,
    slice_nargs: int = 1,
    label_on: Optional[int] = None,
    ordinal_idx_arg: Optional[int] = None,
    flatten_output: bool = True,
) -> Any:
    """Split the input of a function into small batches and call :func:`func` on each batch
    , collect the merged result and return. This is useful when the input is too big to fit into memory

    :param func: function to decorate
    :param batch_size: size of each batch
    :param num_batch: number of batches to take, the rest will be ignored
    :param split_over_axis: split over which axis into batches
    :param merge_over_axis: merge over which axis into a single result
    :param slice_on: the location of the data. When using inside a class,
            ``slice_on`` should take ``self`` into consideration.
    :param slice_nargs: the number of arguments
    :param label_on: the location of the labels. Useful for data with any kind of accompanying labels
    :param ordinal_idx_arg: the location of the ordinal indexes argument. Needed for classes
            where function decorated needs to know the ordinal indexes of the data in the batch
            (Not used when label_on is used)
    :param flatten_output: If this is set to True, the results from different batches will be chained and the returning value is a list of the results. Otherwise, the returning value is a list of lists, in which each element is a list containing the result from one single batch. Note if there is only one batch returned, the returned result is always flatten.
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
            data = args[slice_on : slice_on + slice_nargs]
            b_size = (
                batch_size(data) if callable(batch_size) else batch_size
            ) or getattr(args[0], 'batch_size', None)

            # no batching if b_size is None
            if b_size is None or data is None:
                return func(*args, **kwargs)

            default_logger.debug(
                f'batching enabled for {func.__qualname__} batch_size={b_size} '
                f'num_batch={num_batch} axis={split_over_axis}'
            )

            results = []
            data = (data, args[label_on]) if label_on else data

            yield_slice = [
                isinstance(args[slice_on + i], np.memmap) for i in range(0, slice_nargs)
            ]

            slice_idx = None

            # split the data into batches
            data_iterators = [
                batch_iterator(
                    data[i],
                    b_size,
                    split_over_axis,
                    yield_slice=yield_slice[i],
                )
                for i in range(0, slice_nargs)
            ]

            batch_args = list(copy.copy(args))

            # load the batches of data and feed into the function
            for _data_args in zip(*data_iterators):
                _data_args = list(_data_args)
                for i, (_yield_slice, _arg) in enumerate(zip(yield_slice, _data_args)):
                    if _yield_slice:
                        original_arg = args[slice_on + i]
                        _memmap = np.memmap(
                            original_arg.filename,
                            dtype=original_arg.dtype,
                            mode='r',
                            shape=original_arg.shape,
                        )
                        _data_args[i] = _memmap[_arg]
                        slice_idx = _arg[split_over_axis]
                        if slice_idx.start is None or slice_idx.stop is None:
                            slice_idx = None
                        del _memmap

                    # TODO: figure out what is ordinal_idx_arg
                    if not isinstance(_data_args[i], tuple):
                        if ordinal_idx_arg and slice_idx is not None:
                            batch_args[ordinal_idx_arg] = slice_idx

                batch_args[slice_on : slice_on + slice_nargs] = _data_args

                r = func(*batch_args, **kwargs)

                if r is not None:
                    results.append(r)

            return _merge_results_after_batching(
                results, merge_over_axis, flatten_output
            )

        return arg_wrapper

    if func:
        return _batching(func)
    else:
        return _batching


def single(
    func: Optional[Callable[[Any], np.ndarray]] = None,
    merge_over_axis: int = 0,
    slice_on: int = 1,
    slice_nargs: int = 1,
    flatten_output: bool = False,
) -> Any:
    """Guarantee that the inputs of a function with more than one argument is provided as single instances and not in batches

    :param func: function to decorate
    :param merge_over_axis: merge over which axis into a single result
    :param slice_on: the location of the data. When using inside a class,
            ``slice_on`` should take ``self`` into consideration.
    :param slice_nargs: the number of positional arguments considered as data
    :param flatten_output: If this is set to True, the results from different batches will be chained and the returning value is a list of the results. Otherwise, the returning value is a list of lists, in which each element is a list containing the result from one single batch. Note if there is only one batch returned, the returned result is always flatten.
    :return: the merged result as if run :func:`func` once on the input.

    ..warning:
        data arguments will be taken starting from ``slice_on` to ``slice_on + num_data``

    Example:
        .. highlight:: python
        .. code-block:: python

            class OneByOneCrafter:

                @single
                def craft(self, text: str, id: str) -> Dict:
            ...

    .. note:
        Single multi input decorator will let the user interact with the executor in 3 different ways:
            - Providing batches: (This decorator will make sure that the actual method receives just a single instance)
            - Providing a single instance
            - Providing a single instance through kwargs.

        .. highlight:: python
        .. code-block:: python

            class OneByOneCrafter:
                @single
                def craft(self, text: str, id: str) -> Dict:
                    return {'text': f'{text}-crafted', 'id': f'{id}-crafted'}

            crafter = OneByOneCrafter()

            results = crafted.craft(['text1', 'text2'], ['id1', 'id2'])
            assert len(results) == 2
            assert results[0] == {'text': 'text1-crafted', 'id': 'id1-crafted'}
            assert results[1] == {'text': 'text2-crafted', 'id': 'id2-crafted'}

            result = crafter.craft('text', 'id')
            assert result['text'] == 'text-crafted'
            assert result['id'] == 'id-crafted'

            results = crafted.craft(text='text', id='id')
            assert result['text'] == 'text-crafted'
            assert result['id'] == 'id-crafted'
    """

    def _single_multi_input(func):
        @wraps(func)
        def arg_wrapper(*args, **kwargs):
            # by default data is in args[1:] (self needs to be taken into account)
            args = list(args)
            default_logger.debug(f'batching disabled for {func.__qualname__}')

            data_iterators = args[slice_on : slice_on + slice_nargs]

            if len(args) <= slice_on:
                # like this one can use the function with single kwargs
                return func(*args, **kwargs)
            elif len(args) < slice_on + slice_nargs:
                raise IndexError(
                    f'can not select positional args at {slice_on}: {slice_nargs}, '
                    f'your `args` has {len(args)} arguments.'
                )
            elif (
                len(args) <= slice_on
                or isinstance(data_iterators[0], str)
                or isinstance(data_iterators[0], bytes)
                or not isinstance(data_iterators[0], Iterable)
            ):
                # like this one can use the function with single kwargs
                return func(*args, **kwargs)

            final_result = []
            for new_args in zip(*data_iterators):
                args[slice_on : slice_on + slice_nargs] = new_args
                r = func(*args, **kwargs)

                if r is not None:
                    final_result.append(r)

            return _merge_results_after_batching(
                final_result, merge_over_axis, flatten=flatten_output
            )

        return arg_wrapper

    if func:
        return _single_multi_input(func)
    else:
        return _single_multi_input
