from typing import List, Sequence, TYPE_CHECKING, Union

import numpy as np

if TYPE_CHECKING:
    from ...document import ArrayType
    import scipy
    import scipy.sparse


class ContentPropertyMixin:
    """Helpers that provide faster getter & setter for :attr:`.content` by using protobuf directly. """

    def _check_length(self, target_len: int):
        if target_len != len(self):
            raise ValueError(
                f'Length must match {self!r}, but {target_len} != {len(self)}'
            )

    @property
    def embeddings(self) -> Union[np.ndarray, 'scipy.sparse.csr_matrix']:
        """Return a `np.ndarray` or   `scipy.sparse.csr_matrix` stacking all the `embedding` attributes as rows.

        :return: a ndarray or csr_matrix of embeddings
        """
        # this is more general than self._pb_body[0], gives full compat to DA & DAM
        proto = next(iter(self._pb_body)).embedding

        if proto.dense:

            x_mat = b''.join(d.embedding.dense.buffer for d in self._pb_body)
            if proto.dense.dtype:
                return np.frombuffer(x_mat, dtype=proto.dense.dtype).reshape(
                    (len(self), proto.dense.shape[0])
                )

        if proto.sparse:
            import scipy.sparse

            n_examples = len(self)
            n_features = proto.sparse.shape[1]
            indices_dtype = proto.sparse.indices.dtype
            values_dtype = proto.sparse.values.dtype

            indices_bytes = b''
            values_bytes = b''

            row_indices = []
            for k, pb_body_k in enumerate(self._pb_body):
                indices_bytes += pb_body_k.embedding.sparse.indices.buffer
                values_bytes += pb_body_k.embedding.sparse.values.buffer
                row_indices += [k] * pb_body_k.embedding.sparse.values.shape[0]

            if proto.sparse.values.dtype:
                indices_np = np.frombuffer(indices_bytes, dtype=indices_dtype)
                cols_np = indices_np.reshape(2, -1)[1, :]
                vals_np = np.frombuffer(values_bytes, dtype=values_dtype)
                return scipy.sparse.csr_matrix(
                    (vals_np, (row_indices, cols_np)), shape=(n_examples, n_features)
                )

    @embeddings.setter
    def embeddings(self, value: 'ArrayType'):
        """Set the :attr:`.embedding` of the Documents.

        To remove all embeddings of all Documents:
        .. highlight:: python
        .. code-block:: python

            da.embeddings = None

        :param value: The embedding matrix to set
        """

        if value is None:
            for d in self._pb_body:
                d.ClearField('embedding')
        else:
            emb_shape0 = value.shape[0]
            self._check_length(emb_shape0)

            # the best-effort & universal way to index ArrayType on torch, tf, numpy, scipy.sparse
            for d, j in zip(self, range(emb_shape0)):
                d.embedding = value[j, ...]

    @property
    def blobs(self) -> np.ndarray:
        """Return a `np.ndarray` stacking all :attr:`.blob`.

        The `blob` attributes are stacked together along a newly created first
        dimension (as if you would stack using ``np.stack(X, axis=0)``).

        .. warning:: This operation assumes all blobs have the same shape and dtype.
                 All dtype and shape values are assumed to be equal to the values of the
                 first element in the DocumentArray / DocumentArrayMemmap

        :return: a ndarray of blobs
        """
        x_mat = b''.join(d.blob.dense.buffer for d in self._pb_body)
        proto = next(iter(self._pb_body)).blob.dense

        if proto.dtype:
            return np.frombuffer(x_mat, dtype=proto.dtype).reshape(
                (len(self), *proto.shape)
            )

    @blobs.setter
    def blobs(self, value: 'ArrayType'):
        """Set :attr:`.blob` of the Documents. To clear all :attr:`blob`, set it to ``None``.

        :param value: The blob array to set. The first axis is the "row" axis.
        """

        if value is None:
            for d in self._pb_body:
                d.ClearField('blob')
        else:
            blobs_shape0 = value.shape[0]
            self._check_length(blobs_shape0)

            # the best-effort & universal way to index ArrayType on torch, tf, numpy, scipy.sparse
            for d, j in zip(self, range(blobs_shape0)):
                d.blob = value[j, ...]

    @property
    def texts(self) -> List[str]:
        """Get :attr:`.text` of all Documents

        :return: a list of texts
        """
        return [d.text for d in self._pb_body]

    @texts.setter
    def texts(self, value: Sequence[str]):
        """Set :attr:`.text` for all Documents. To clear all :attr:`text`, set it to ``None``.

        :param value: A sequence of texts to set, should be the same length as the
            number of Documents
        """
        if value is None:
            for d in self._pb_body:
                d.ClearField('text')
        else:
            self._check_length(len(value))

            for doc, text in zip(self._pb_body, value):
                doc.text = text

    @property
    def buffers(self) -> List[bytes]:
        """Get the buffer attribute of all Documents.

        :return: a list of buffers
        """
        return [d.buffer for d in self._pb_body]

    @buffers.setter
    def buffers(self, value: List[bytes]):
        """Set the buffer attribute for all Documents. To clear all :attr:`buffer`, set it to ``None``.

        :param value: A sequence of buffer to set, should be the same length as the
            number of Documents
        """

        if value is None:
            for d in self._pb_body:
                d.ClearField('buffer')
        else:
            self._check_length(len(value))

            for doc, buffer in zip(self._pb_body, value):
                doc.buffer = buffer
