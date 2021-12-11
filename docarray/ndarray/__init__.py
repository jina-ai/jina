from typing import TYPE_CHECKING, TypeVar, Tuple, Sequence, Iterator

import numpy as np

from ..base import BaseProtoView
from ..proto.docarray_pb2 import NdArrayProto

if TYPE_CHECKING:
    import scipy.sparse
    import tensorflow
    import torch

    ArrayType = TypeVar(
        'ArrayType',
        np.ndarray,
        scipy.sparse.spmatrix,
        tensorflow.SparseTensor,
        tensorflow.Tensor,
        torch.Tensor,
        Sequence[float],
    )

    from .. import Document

__all__ = ['NdArray']


class NdArray(BaseProtoView):
    """
    A base class for containing the protobuf message of NdArray. It defines interfaces for easier get/set value.

    Do not use this class directly. Subclass should be used.

    :param proto: the protobuf message, when not given then create a new one via :meth:`get_null_proto`
    """

    _PbMsg = NdArrayProto

    def numpy(self) -> 'np.ndarray':
        """Return the value always in :class:`numpy.ndarray` regardless the framework type.

        :return: the value in :class:`numpy.ndarray`.
        """
        v = self.value
        if self.is_sparse:
            if hasattr(v, 'todense'):
                v = v.todense()
            elif hasattr(v, 'to_dense'):
                v = v.to_dense()
            elif self.framework == 'tensorflow':
                import tensorflow as tf

                if isinstance(v, tf.SparseTensor):
                    v = tf.sparse.to_dense(v)

        if hasattr(v, 'numpy'):
            v = v.numpy()
        return v

    @property
    def value(self) -> 'ArrayType':
        """Return the value in original framework type

        :return: the value of in numpy, scipy, tensorflow, pytorch type."""

        if self.is_sparse:
            if self.framework == 'scipy':
                idx, val, shape = self._get_raw_sparse_array()
                from scipy.sparse import coo_matrix

                x = coo_matrix((val, idx.T), shape=shape)
                sp_format = self._pb_body.parameters['sparse_format']
                if sp_format == 'bsr':
                    return x.tobsr()
                elif sp_format == 'csc':
                    return x.tocsc()
                elif sp_format == 'csr':
                    return x.tocsr()
                elif sp_format == 'coo':
                    return x
            elif self.framework == 'tensorflow':
                idx, val, shape = self._get_raw_sparse_array()
                from tensorflow import SparseTensor

                return SparseTensor(idx, val, shape)
            elif self.framework == 'torch':
                idx, val, shape = self._get_raw_sparse_array()
                from torch import sparse_coo_tensor

                return sparse_coo_tensor(idx, val, shape)
        else:
            if self.framework in {'numpy', 'torch', 'paddle', 'tensorflow'}:
                x = _get_dense_array(self._pb_body.dense)
                return _to_framework_array(x, self.framework)

    @staticmethod
    def ravel(value: 'ArrayType', docs: Iterator['Document'], field: str) -> None:
        """Ravel :attr:`value` into ``doc.field`` of each documents

        :param docs: the docs to set
        :param field: the field of the doc to set
        :param value: the value to be set on ``doc.field``
        """

        use_get_row = False
        if hasattr(value, 'getformat'):
            # for scipy only
            sp_format = value.getformat()
            if sp_format in {'bsr', 'coo'}:
                # for BSR and COO, they dont implement [j, ...] in scipy
                # but they offer get_row() API which implicitly translate the
                # sparse row into CSR format, hence needs to convert back
                # not very efficient, but this is the best we can do.
                use_get_row = True

        if use_get_row:
            emb_shape0 = value.shape[0]
            for d, j in zip(docs, range(emb_shape0)):
                row = getattr(value.getrow(j), f'to{sp_format}')()
                setattr(d, field, row)
        elif isinstance(value, (list, tuple)):
            for d, j in zip(docs, value):
                setattr(d, field, j)
        else:
            emb_shape0 = value.shape[0]
            for d, j in zip(docs, range(emb_shape0)):
                setattr(d, field, value[j, ...])

    @staticmethod
    def unravel(protos: Sequence[NdArrayProto]) -> 'ArrayType':
        """Unravel many ndarray-like proto in one-shot, by following the shape
        and dtype of the first proto.

        :param protos: a list of ndarray protos
        :return: a framework ndarray
        """
        first = NdArray(protos[0])
        framework, is_sparse = first.framework, first.is_sparse

        if is_sparse:
            if framework in {'tensorflow'}:
                raise NotImplementedError(
                    f'fast ravel on sparse {framework} is not supported yet.'
                )

            val = _unravel_dense_array(
                (d.sparse.values.buffer for d in protos),
                shape=[],
                dtype=first.sparse.values.dtype,
            )

            shape = [len(protos)] + list(first.sparse.shape)

            all_ds = []
            for j, p in enumerate(protos):
                _d = _get_dense_array(p.sparse.indices)

                if framework == 'torch':
                    _idx = np.array([j] * _d.shape[-1], dtype=np.int32).reshape([1, -1])
                    _d = np.vstack([_idx, _d])
                if framework == 'scipy':
                    _idx = np.array([j] * _d.shape[0], dtype=np.int32)
                    _d = np.stack([_idx, _d[:, 1]], axis=-1)
                all_ds.append(_d)

            if framework == 'torch':
                idx = np.concatenate(all_ds, axis=-1)
                from torch import sparse_coo_tensor

                return sparse_coo_tensor(idx, val, shape)
            if framework == 'scipy':
                # scipy sparse is limited to ndim=2
                idx = np.concatenate(all_ds, axis=0)
                sp_format = first._pb_body.parameters['sparse_format']
                shape = [len(protos), first.sparse.shape[-1]]
                if sp_format == 'csc':
                    from scipy.sparse import csc_matrix

                    return csc_matrix((val, idx.T), shape=shape)
                if sp_format == 'csr':
                    from scipy.sparse import csr_matrix

                    return csr_matrix((val, idx.T), shape=shape)
                if sp_format == 'coo':
                    from scipy.sparse import coo_matrix

                    return coo_matrix((val, idx.T), shape=shape)
                if sp_format == 'bsr':
                    from scipy.sparse import bsr_matrix

                    return bsr_matrix((val, idx.T), shape=shape)

        else:
            if framework in {'numpy', 'torch', 'paddle', 'tensorflow'}:
                x = _unravel_dense_array(
                    (d.dense.buffer for d in protos),
                    shape=list(first.dense.shape),
                    dtype=first.dense.dtype,
                )
                return _to_framework_array(x, framework)

    @value.setter
    def value(self, value: 'ArrayType'):
        """Set the value from numpy, scipy, tensorflow, pytorch type to protobuf.

        :param value: the framework ndarray to be set.
        """
        framework, is_sparse = get_array_type(value)

        if framework == 'jina':
            # it is Jina's NdArray, simply copy it
            self._pb_body.cls_name = 'numpy'
            self._pb_body.CopyFrom(value._pb_body)
        elif framework == 'jina_proto':
            self._pb_body.cls_name = 'numpy'
            self._pb_body.CopyFrom(value)
        else:
            if is_sparse:
                if framework == 'scipy':
                    self._pb_body.parameters['sparse_format'] = value.getformat()
                    self._set_scipy_sparse(value)
                if framework == 'tensorflow':
                    self._set_tf_sparse(value)
                if framework == 'torch':
                    self._set_torch_sparse(value)
            else:
                if framework == 'numpy':
                    self._pb_body.cls_name = 'numpy'
                    _set_dense_array(value, self._pb_body.dense)
                if framework == 'python':
                    self._pb_body.cls_name = 'numpy'
                    _set_dense_array(np.array(value), self._pb_body.dense)
                if framework == 'tensorflow':
                    self._pb_body.cls_name = 'tensorflow'
                    _set_dense_array(value.numpy(), self._pb_body.dense)
                if framework == 'torch':
                    self._pb_body.cls_name = 'torch'
                    _set_dense_array(value.detach().cpu().numpy(), self._pb_body.dense)
                if framework == 'paddle':
                    self._pb_body.cls_name = 'paddle'
                    _set_dense_array(value.numpy(), self._pb_body.dense)

    @property
    def is_sparse(self) -> bool:
        """Check if the object represents a sparse ndarray.

        :return: True if the underlying ndarray is sparse
        """
        return self._pb_body.WhichOneof('content') == 'sparse'

    @property
    def framework(self) -> str:
        """Return the framework name of this ndarray object

        :return: the framework name
        """
        return self._pb_body.cls_name

    def _set_scipy_sparse(self, value: 'scipy.sparse.spmatrix'):
        v = value.tocoo(copy=True)
        indices = np.stack([v.row, v.col], axis=1)
        _set_dense_array(indices, self._pb_body.sparse.indices)
        _set_dense_array(v.data, self._pb_body.sparse.values)
        self._pb_body.sparse.ClearField('shape')
        self._pb_body.sparse.shape.extend(v.shape)
        self._pb_body.cls_name = 'scipy'

    def _set_tf_sparse(self, value: 'tensorflow.SparseTensor'):
        _set_dense_array(value.indices.numpy(), self._pb_body.sparse.indices)
        _set_dense_array(value.values.numpy(), self._pb_body.sparse.values)
        self._pb_body.sparse.ClearField('shape')
        self._pb_body.sparse.shape.extend(value.shape)
        self._pb_body.cls_name = 'tensorflow'

    def _set_torch_sparse(self, value):
        _set_dense_array(
            value.coalesce().indices().numpy(), self._pb_body.sparse.indices
        )
        _set_dense_array(value.coalesce().values().numpy(), self._pb_body.sparse.values)
        self._pb_body.sparse.ClearField('shape')
        self._pb_body.sparse.shape.extend(list(value.size()))
        self._pb_body.cls_name = 'torch'

    def _get_raw_sparse_array(self):
        idx = _get_dense_array(self._pb_body.sparse.indices)
        val = _get_dense_array(self._pb_body.sparse.values)
        shape = list(self._pb_body.sparse.shape)
        return idx, val, shape


def _get_dense_array(source):
    if source.buffer:
        x = np.frombuffer(source.buffer, dtype=source.dtype)
        return x.reshape(source.shape)
    elif len(source.shape) > 0:
        return np.zeros(source.shape)


def _set_dense_array(value, target):
    target.buffer = value.tobytes()
    target.ClearField('shape')
    target.shape.extend(list(value.shape))
    target.dtype = value.dtype.str


def get_array_type(array: 'ArrayType') -> Tuple[str, bool]:
    """Get the type of ndarray without importing the framework

    :param array: any array, scipy, numpy, tf, torch, etc.
    :return: a tuple where the first element represents the framework, the second represents if it is sparse array
    """
    module_tags = array.__class__.__module__.split('.')
    class_name = array.__class__.__name__

    if isinstance(array, (list, tuple)):
        return 'python', False

    if 'numpy' in module_tags:
        return 'numpy', False

    if 'jina' in module_tags:
        if class_name == 'NdArray':
            return 'jina', False  # sparse or not is irrelevant

    if 'docarray_pb2' in module_tags:
        if class_name == 'NdArrayProto':
            return 'jina_proto', False  # sparse or not is irrelevant

    if 'tensorflow' in module_tags:
        if class_name == 'SparseTensor':
            return 'tensorflow', True
        if class_name == 'Tensor' or class_name == 'EagerTensor':
            return 'tensorflow', False

    if 'torch' in module_tags and class_name == 'Tensor':
        return 'torch', array.is_sparse

    if 'paddle' in module_tags and class_name == 'Tensor':
        # Paddle does not support sparse tensor on 11/8/2021
        # https://github.com/PaddlePaddle/Paddle/issues/36697
        return 'paddle', False

    if 'scipy' in module_tags and 'sparse' in module_tags:
        return 'scipy', True

    raise TypeError(f'can not determine the array type: {module_tags}.{class_name}')


def _to_framework_array(x, framework):
    if framework == 'numpy':
        return x
    elif framework == 'tensorflow':
        from tensorflow import convert_to_tensor

        return convert_to_tensor(x)
    elif framework == 'torch':
        from torch import from_numpy

        return from_numpy(x)
    elif framework == 'paddle':
        from paddle import to_tensor

        return to_tensor(x)


def _unravel_dense_array(source, shape, dtype):
    x_mat = b''.join(source)
    shape = [-1] + shape
    return np.frombuffer(x_mat, dtype=dtype).reshape(shape)


import google.protobuf.json_format
from google.protobuf.json_format import _Printer, _Parser


class _PrinterWithNdArraySupport(_Printer):
    def _MessageToJsonObject(self, message):
        message_descriptor = message.DESCRIPTOR
        full_name = message_descriptor.full_name
        if full_name == 'docarray.NdArrayProto':
            return NdArray(message).numpy().tolist()
        else:
            return super()._MessageToJsonObject(message)


class _ParseWithNdArraySupport(_Parser):
    def ConvertMessage(self, value, message):
        message_descriptor = message.DESCRIPTOR
        full_name = message_descriptor.full_name
        if full_name == 'docarray.NdArrayProto':
            na = NdArray()
            na.value = value
            message.CopyFrom(na._pb_body)
            return message
        else:
            return super().ConvertMessage(value, message)


google.protobuf.json_format._Printer = _PrinterWithNdArraySupport
google.protobuf.json_format._Parser = _ParseWithNdArraySupport
