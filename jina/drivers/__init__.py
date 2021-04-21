__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import inspect
import typing
from functools import wraps
from typing import (
    Any,
    Dict,
    Callable,
    Tuple,
    Optional,
    Sequence,
    Iterable,
    List,
    Union,
)

import numpy as np
from google.protobuf.struct_pb2 import Struct

from ..enums import OnErrorStrategy
from ..excepts import LengthMismatchException
from ..executors.compound import CompoundExecutor
from ..executors.decorators import wrap_func
from ..helper import (
    convert_tuple_to_list,
    cached_property,
    find_request_binding,
    _canonical_request_name,
)
from ..jaml import JAMLCompatible
from ..types.querylang import QueryLang
from ..types.sets import DocumentSet

# noinspection PyUnreachableCode
if False:
    # fix type-hint complain for sphinx and flake
    from ..peapods.runtimes.zmq.zed import ZEDRuntime
    from ..executors import AnyExecutor
    from ..logging.logger import JinaLogger
    from ..types.message import Message
    from ..types.request import Request
    from ..types.sets import QueryLangSet
    from ..types.document import Document


def store_init_kwargs(func: Callable) -> Callable:
    """Mark the args and kwargs of :func:`__init__` later to be stored via :func:`save_config` in YAML

    :param func: the Callable to wrap
    :return: the wrapped Callable
    """

    @wraps(func)
    def _arg_wrapper(self, *args, **kwargs):
        if func.__name__ != '__init__':
            raise TypeError(
                'this decorator should only be used on __init__ method of a driver'
            )
        taboo = {'self', 'args', 'kwargs'}
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

        if self.store_args_kwargs:
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

    return _arg_wrapper


class QuerySetReader:
    """
    :class:`QuerySetReader` allows a driver to read arguments from the protobuf message. This allows a
    driver to override its behavior based on the message it receives. Extremely useful in production, for example,
    get ``top_k`` results, doing pagination, filtering.

    To register the field you want to read from the message, simply register them in :meth:`__init__`.
    For example, ``__init__(self, arg1, arg2, **kwargs)`` will allow the driver to read field ``arg1`` and ``arg2`` from
    the message. When they are not found in the message, the value ``_arg1`` and ``_arg2`` will be used. Note the underscore
    prefix.

    .. note::
        - To set default value of ``arg1``, use ``self._arg1 =``, note the underscore in the front.
        - To access ``arg1``, simply use ``self.arg1``. It automatically switch between default ``_arg1`` and ``arg1`` from the request.

    For successful value reading, the following condition must be met:

        - the ``name`` in the proto must match with the current class name
        - the ``disabled`` field in the proto should not be ``False``
        - the ``priority`` in the proto should be strictly greater than the driver's priority (by default is 0)
        - the field name must exist in proto's ``parameters``

    .. warning::
        For the sake of cooperative multiple inheritance, do NOT implement :meth:`__init__` for this class
    """

    @property
    def as_querylang(self):
        """Render as QueryLang parameters.


        .. # noqa: DAR201"""
        parameters = {
            name: getattr(self, name) for name in self._init_kwargs_dict.keys()
        }
        return QueryLang(
            {
                'name': self.__class__.__name__,
                'priority': self._priority,
                'parameters': parameters,
            }
        )

    def _get_parameter(self, key: str, default: Any):
        if getattr(self, 'queryset', None):
            for q in self.queryset:
                if (
                    not q.disabled
                    and self.__class__.__name__ == q.name
                    and q.priority > self._priority
                    and key in q.parameters
                ):
                    ret = q.parameters[key]
                    return dict(ret) if isinstance(ret, Struct) else ret
        return getattr(self, f'_{key}', default)

    def __getattr__(self, name: str):
        # https://docs.python.org/3/reference/datamodel.html#object.__getattr__
        if name == '_init_kwargs_dict':
            # raise attribute error to avoid recursive call
            raise AttributeError
        if name in self._init_kwargs_dict:
            return self._get_parameter(name, default=self._init_kwargs_dict[name])
        raise AttributeError


class DriverType(type(JAMLCompatible), type):
    """A meta class representing a Driver

    When a new Driver is created, it gets registered
    """

    def __new__(cls, *args, **kwargs):
        """Create and register a new class with this meta class.

        :param args: additional positional arguments which are just used for the parent initialization
        :param kwargs: additional key value arguments which are just used for the parent initialization
        :return: the newly registered class
        """
        _cls = super().__new__(cls, *args, **kwargs)
        return cls.register_class(_cls)

    @staticmethod
    def register_class(cls):
        """Register a class

        :param cls: the class
        :return: the class, after being registered
        """
        reg_cls_set = getattr(cls, '_registered_class', set())
        if cls.__name__ not in reg_cls_set or getattr(cls, 'force_register', False):
            wrap_func(cls, ['__init__'], store_init_kwargs)
            # wrap_func(cls, ['__call__'], as_reduce_method)

            reg_cls_set.add(cls.__name__)
            setattr(cls, '_registered_class', reg_cls_set)
        return cls


class BaseDriver(JAMLCompatible, metaclass=DriverType):
    """A :class:`BaseDriver` is a logic unit above the :class:`jina.peapods.runtimes.zmq.zed.ZEDRuntime`.
    It reads the protobuf message, extracts/modifies the required information and then return
    the message back to :class:`jina.peapods.runtimes.zmq.zed.ZEDRuntime`.

    A :class:`BaseDriver` needs to be :attr:`attached` to a :class:`jina.peapods.runtimes.zmq.zed.ZEDRuntime` before
    using. This is done by :func:`attach`. Note that a deserialized :class:`BaseDriver` from file is always unattached.

    :param priority: the priority of its default arg values (hardcoded in Python). If the
         received ``QueryLang`` has a higher priority, it will override the hardcoded value
    :param args: not used (kept to maintain interface)
    :param kwargs: not used (kept to maintain interface)
    """

    store_args_kwargs = False  #: set this to ``True`` to save ``args`` (in a list) and ``kwargs`` (in a map) in YAML config

    def __init__(self, priority: int = 0, *args, **kwargs):
        self.attached = False  # : represent if this driver is attached to a
        # :class:`jina.peapods.runtimes.zmq.zed.ZEDRuntime` (& :class:`jina.executors.BaseExecutor`)
        self.runtime = None  # type: Optional['ZEDRuntime']
        self._priority = priority

    def attach(self, runtime: 'ZEDRuntime', *args, **kwargs) -> None:
        """Attach this driver to a :class:`jina.peapods.runtimes.zmq.zed.ZEDRuntime`

        :param runtime: the pea to be attached
        :param args: not used (kept to maintain interface)
        :param kwargs: not used (kept to maintain interface)
        """
        self.runtime = runtime
        self.attached = True

    @property
    def req(self) -> 'Request':
        """Get the current (typed) request, shortcut to ``self.runtime.request``


        .. # noqa: DAR201
        """
        return self.runtime.request

    @property
    def partial_reqs(self) -> Sequence['Request']:
        """The collected partial requests under the current ``request_id``


        .. # noqa: DAR401


        .. # noqa: DAR201
        """
        if self.expect_parts > 1:
            return self.runtime.partial_requests
        else:
            raise ValueError(
                f'trying to access all partial requests, '
                f'but {self.runtime} has only one message'
            )

    @property
    def expect_parts(self) -> int:
        """The expected number of partial messages


        .. # noqa: DAR201
        """
        return self.runtime.expect_parts

    @property
    def docs(self) -> 'DocumentSet':
        """The DocumentSet after applying the traversal


        .. # noqa: DAR201"""
        from ..types.sets import DocumentSet

        if self.expect_parts > 1:
            return DocumentSet([d for r in reversed(self.partial_reqs) for d in r.docs])
        else:
            return self.req.docs

    @property
    def msg(self) -> 'Message':
        """Get the current request, shortcut to ``self.runtime.message``


        .. # noqa: DAR201
        """
        return self.runtime.message

    @property
    def queryset(self) -> 'QueryLangSet':
        """


        .. # noqa: DAR101


        .. # noqa: DAR102


        .. # noqa: DAR201
        """
        if self.msg:
            return self.msg.request.queryset
        else:
            return []

    @property
    def logger(self) -> 'JinaLogger':
        """Shortcut to ``self.runtime.logger``


        .. # noqa: DAR201
        """
        return self.runtime.logger

    def __call__(self, *args, **kwargs) -> None:
        """


        .. # noqa: DAR102


        .. # noqa: DAR101
        """
        raise NotImplementedError

    def __eq__(self, other):
        return self.__class__ == other.__class__

    def __getstate__(self) -> Dict[str, Any]:
        """
        Unlike `Executor`, driver is stateless.

        Therefore, on every save, it creates a new & empty driver object and save it.
        :return: the state in dict form
        """

        d = dict(self.__class__(**self._init_kwargs_dict).__dict__)
        return d


class ContextAwareRecursiveMixin:
    """
    The full data structure version of :class:`FlatRecursiveMixin`, to be mixed in with :class:`BaseRecursiveDriver`.
    It uses :meth:`traverse` in :class:`DocumentSet` and allows direct manipulation of Chunk-/Match-/DocumentSets.

    .. seealso::
       https://github.com/jina-ai/jina/issues/1932

    """

    def __call__(self, *args, **kwargs):
        """Traverse with _apply_all

        :param args: args forwarded to ``_apply_all``
        :param kwargs: kwargs forwarded to ``_apply_all``
        """
        document_sets = self.docs.traverse(self._traversal_paths)
        self._apply_all(document_sets, *args, **kwargs)

    def _apply_all(
        self,
        doc_sequences: Iterable['DocumentSet'],
        *args,
        **kwargs,
    ) -> None:
        """Apply function works on an Iterable of DocumentSet, modify the docs in-place.

        Each DocumentSet refers to a leaf (e.g. roots, matches or chunks wrapped
        in a :class:`jina.DocumentSet`) in the traversal_paths. Modifications on the
        DocumentSets (e.g. adding or deleting Documents) are directly applied on the underlying objects.
        Adding a chunk to a ChunkSet results in adding a chunk to the parent Document.

        :param doc_sequences: the Documents that should be handled
        :param args: driver specific arguments, which might be forwarded to the Executor
        :param kwargs: driver specific arguments, which might be forwarded to the Executor
        """


class FlatRecursiveMixin:
    """
    The batch optimized version of :class:`ContextAwareRecursiveMixin`, to be mixed in with :class:`BaseRecursiveDriver`.
    It uses :meth:`traverse_flattened_per_path` in :class:`DocumentSet` and yield much better performance
    when no context is needed and batching is possible.

    .. seealso::
       https://github.com/jina-ai/jina/issues/1932

    """

    def __call__(self, *args, **kwargs):
        """Traverse with _apply_all

        :param args: args forwarded to ``_apply_all``
        :param kwargs: kwargs forwarded to ``_apply_all``
        """
        path_documents = self.docs.traverse_flattened_per_path(self._traversal_paths)
        for documents in path_documents:
            if documents:
                self._apply_all(documents, *args, **kwargs)

    def _apply_all(
        self,
        docs: 'DocumentSet',
        *args,
        **kwargs,
    ) -> None:
        """Apply function works on a list of docs, modify the docs in-place.

        The list refers to all reachable leaves of a single ``traversal_path``.

        :param docs: the Documents that should be handled
        :param args: driver specific arguments, which might be forwarded to the Executor
        :param kwargs: driver specific arguments, which might be forwarded to the Executor

        """


class DocsExtractUpdateMixin:
    """
    A Driver pattern for extracting attributes from Documents, feeding to an executor and updating the Documents with
    the results.

    Drivers equipped with this mixin will have :method:`_apply_all` inherited.

    The :method:`_apply_all` implements the following logics:
        - From ``docs``, it extracts the attributes defined :method:`exec_fn`'s arguments.
        - It feeds the attributes to the bind executor's :method:`exec_fn`.
        - It updates ``docs`` with results returned from :method:`exec_fn`

    The following shortcut logics are implemented:
        - while extracting: attributes defined :method:`exec_fn`'s arguments are extracted from ``docs``;
        - while extracting: attributes annotated with ``ndarray`` are stacked into Numpy NdArray objects;
        - while updating: if ``exec_fn`` returns a List of Dict, then ``doc.set_attrs(**exec_result)`` is called;
        - while updating: if ``exec_fn`` returns a Document, then ``doc.update(exec_result)` is called.
        - while updating: if none of above applies, then calling :meth:`update_single_doc`

    To override the update behavior, you can choose to override:
        - :meth:`update_docs` if you want to modify the behavior of updating docs in bulk
        - :meth:`update_single_doc` if you want to modify the behavior of updating a single doc
    """

    def _apply_all(self, docs: 'DocumentSet') -> None:
        """Apply function works on a list of docs, modify the docs in-place.

        The list refers to all reachable leaves of a single ``traversal_path``.

        :param docs: the Documents that should be handled
        """

        contents, docs_pts = docs.extract_docs(
            *self._exec_fn_required_keys,
            stack_contents=self._exec_fn_required_keys_is_ndarray,
        )

        if docs_pts:
            if len(self._exec_fn_required_keys) > 1:
                exec_results = self.exec_fn(*contents)
            else:
                exec_results = self.exec_fn(contents)

            if exec_results is not None:
                # if exec_fn returns None then exec_fn is assumed to be immutable wrt. doc, hence skipped

                try:
                    len_results = len(exec_results)
                except:
                    try:
                        len_results = exec_results.shape[0]
                    except:
                        len_results = None

                if len(docs_pts) != len_results:
                    msg = (
                        f'mismatched {len(docs_pts)} docs from level {docs_pts[0].granularity} '
                        f'and length of returned: {len_results}, their length must be the same'
                    )
                    raise LengthMismatchException(msg)

                self.update_docs(docs_pts, exec_results)

    def update_docs(
        self,
        docs_pts: 'DocumentSet',
        exec_results: Union[List[Dict], List['Document'], Any],
    ) -> None:
        """
        Update Documents with the Executor returned results.

        :param: docs_pts: the set of document to be updated
        :param: exec_results: the results from :meth:`exec_fn`
        """
        from ..types.document import Document

        if self._exec_fn_return_is_ndarray and not isinstance(exec_results, np.ndarray):
            r_type = type(exec_results).__name__
            if r_type in {'EagerTensor', 'Tensor', 'list'}:
                exec_results = np.array(exec_results, dtype=np.float32)
            else:
                raise TypeError(f'unrecognized type {exec_results!r}')

        for doc, exec_result in zip(docs_pts, exec_results):
            if isinstance(exec_result, dict):
                doc.set_attrs(**exec_result)
            elif isinstance(exec_result, Document):
                # doc id should not be override with this method
                doc.update(exec_result, exclude_fields=('id',))
            else:
                self.update_single_doc(doc, exec_result)

    def update_single_doc(self, doc: 'Document', exec_result: Any) -> None:
        """Update a single Document with the Executor returned result.

        :param doc: the Document object
        :param exec_result: the single result from :meth:`exec_fn`
        """
        raise NotImplementedError

    @cached_property
    def _exec_fn_required_keys(self) -> List[str]:
        """Get the arguments of :attr:`exec_fn`.

        If ``strict_method_args`` set, then all arguments of :attr:`exec_fn` must be valid :class:`Document` attribute.

        :return: a list of supported arguments
        """

        if not self.exec_fn:
            raise ValueError(
                f'`exec_fn` is None, maybe {self} is not attached? call `self.attach`.'
            )

        required_keys = [
            k
            for k in inspect.getfullargspec(inspect.unwrap(self.exec_fn)).args
            if k != 'self'
        ]
        if not required_keys:
            raise AttributeError(f'{self.exec_fn} takes no argument.')

        if self._strict_method_args:
            from ..proto import jina_pb2
            from .. import Document

            support_keys = Document.get_all_attributes()
            unrecognized_keys = set(required_keys).difference(support_keys)
            if unrecognized_keys:
                camel_keys = set(
                    jina_pb2.DocumentProto().DESCRIPTOR.fields_by_camelcase_name
                )
                legacy_keys = {'data'}
                unrecognized_camel_keys = unrecognized_keys.intersection(camel_keys)
                if unrecognized_camel_keys:
                    raise AttributeError(
                        f'{unrecognized_camel_keys} are supported but you give them in CamelCase, '
                        f'please rewrite them in canonical form.'
                    )
                elif unrecognized_keys.intersection(legacy_keys):
                    raise AttributeError(
                        f'{unrecognized_keys.intersection(legacy_keys)} is now deprecated and not a valid argument of '
                        'the executor function, '
                        'please change `data` to `content: \'np.ndarray\'` in your executor function. '
                        'details: https://github.com/jina-ai/jina/pull/2313/'
                    )
                else:
                    raise AttributeError(
                        f'{unrecognized_keys} are invalid Document attributes, must come from {support_keys}'
                    )

        return required_keys

    @cached_property
    def _exec_fn_required_keys_is_ndarray(self) -> List[bool]:
        """Return a list of boolean indicators for showing if a key is annotated as ndarray

        :return: a list of boolean idicator, True if the corresponding key is annotated as ndarray
        """

        anno = typing.get_type_hints((inspect.unwrap(self.exec_fn)))
        return [anno.get(k, None) == np.ndarray for k in self._exec_fn_required_keys]

    @cached_property
    def _exec_fn_return_is_ndarray(self) -> bool:
        """Return a boolean value for showing if the return of :meth:`exec_fn` is annotated as `ndarray`

        :return: a bool indicator
        """
        return (
            typing.get_type_hints((inspect.unwrap(self.exec_fn))).get('return', None)
            == np.ndarray
        )


class BaseRecursiveDriver(BaseDriver):
    """A :class:`BaseRecursiveDriver` is an abstract Driver class containing information about the `traversal_paths`
    that a `Driver` must apply its logic.
    It is intended to be mixed in with either :class:`FlatRecursiveMixin` or :class:`ContextAwareRecursiveMixin`
    """

    def __init__(self, traversal_paths: Tuple[str] = ('c', 'r'), *args, **kwargs):
        """Initialize a :class:`BaseRecursiveDriver`

        :param traversal_paths: Describes the leaves of the document tree on which _apply_all are called
        :param args: additional positional arguments which are just used for the parent initialization
        :param kwargs: additional key value arguments which are just used for the parent initialization
        """
        super().__init__(*args, **kwargs)
        self._traversal_paths = [path.lower() for path in traversal_paths]


class BaseExecutableDriver(BaseRecursiveDriver):
    """A :class:`BaseExecutableDriver` is an intermediate logic unit between the :class:`jina.peapods.runtimes.zmq.zed.ZEDRuntime` and :class:`jina.executors.BaseExecutor`
    It reads the protobuf message, extracts/modifies the required information and then sends to the :class:`jina.executors.BaseExecutor`,
    finally it returns the message back to :class:`jina.peapods.runtimes.zmq.zed.ZEDRuntime`.

    A :class:`BaseExecutableDriver` needs to be :attr:`attached` to a :class:`jina.peapods.runtimes.zmq.zed.ZEDRuntime` and :class:`jina.executors.BaseExecutor` before using.
    This is done by :func:`attach`. Note that a deserialized :class:`BaseDriver` from file is always unattached.
    """

    def __init__(
        self,
        executor: Optional[str] = None,
        method: Optional[str] = None,
        strict_method_args: bool = True,
        *args,
        **kwargs,
    ):
        """Initialize a :class:`BaseExecutableDriver`

        :param executor: the name of the sub-executor, only necessary when :class:`jina.executors.compound.CompoundExecutor` is used
        :param method: the function name of the executor that the driver feeds to
        :param strict_method_args: if set, then the input args of ``executor.method`` must be valid :class:`Document` attributes
        :param args: additional positional arguments which are just used for the parent initialization
        :param kwargs: additional key value arguments which are just used for the parent initialization
        """
        super().__init__(*args, **kwargs)
        self._executor_name = executor
        self._method_name = method
        self._strict_method_args = strict_method_args
        self._exec = None
        self._exec_fn = None

    @property
    def exec(self) -> 'AnyExecutor':
        """the executor that to which the instance is attached


        .. # noqa: DAR201
        """
        return self._exec

    @property
    def exec_fn(self) -> Callable:
        """the function of :func:`jina.executors.BaseExecutor` to call

        :return: the Callable to execute in the driver
        """
        if not self.runtime:
            return self._exec_fn
        elif (
            not self.msg.is_error
            or self.runtime.args.on_error_strategy < OnErrorStrategy.SKIP_EXECUTOR
        ):
            return self._exec_fn
        else:
            return lambda *args, **kwargs: None

    def attach(
        self, executor: 'AnyExecutor', req_type: Optional[str] = None, *args, **kwargs
    ) -> None:
        """Attach the driver to a :class:`jina.executors.BaseExecutor`

        :param executor: the executor to which we attach
        :param req_type: the request type to attach to
        :param args: additional positional arguments for the call of super().attach()
        :param kwargs: additional key value arguments for the call of super().attach()
        """
        super().attach(*args, **kwargs)
        if self._executor_name and isinstance(executor, CompoundExecutor):
            if self._executor_name in executor:
                self._exec = executor[self._executor_name]
            else:
                for c in executor.components:
                    if any(
                        t.__name__ == self._executor_name for t in type.mro(c.__class__)
                    ):
                        self._exec = c
                        break
            if self._exec is None:
                self.logger.critical(
                    f'fail to attach the driver to {executor}, '
                    f'no executor is named or typed as {self._executor_name}'
                )
        else:
            self._exec = executor

        if not self._method_name:
            decor_bindings = find_request_binding(self.exec.__class__)
            if req_type:
                canonic_name = _canonical_request_name(req_type)
            if req_type and canonic_name in decor_bindings:
                self._method_name = decor_bindings[canonic_name]
            elif 'default' in decor_bindings:
                self._method_name = decor_bindings['default']

        if self._method_name:
            self._exec_fn = getattr(self.exec, self._method_name)

    def __getstate__(self) -> Dict[str, Any]:
        """Do not save the executor and executor function, as it would be cross-referencing and unserializable.
        In other words, a deserialized :class:`BaseExecutableDriver` from file is always unattached.

        :return: dictionary of state
        """
        d = super().__getstate__()
        if '_exec' in d:
            del d['_exec']
        if '_exec_fn' in d:
            del d['_exec_fn']
        return d
