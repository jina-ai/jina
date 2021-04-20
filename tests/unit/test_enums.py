from jina.enums import EmbeddingClsType


def test_embedding_cls_type():
    dense = EmbeddingClsType.DENSE
    assert dense.is_dense
    assert not dense.is_sparse
    assert not dense.is_torch
    assert not dense.is_tf
    assert not dense.is_scipy
    assert not dense.is_scipy_stackable
    assert dense.scipy_cls_type is None

    scipy_coo = EmbeddingClsType.SCIPY_COO
    assert not scipy_coo.is_dense
    assert not scipy_coo.is_torch
    assert not scipy_coo.is_tf
    assert scipy_coo.is_sparse
    assert scipy_coo.is_scipy
    assert scipy_coo.is_scipy_stackable
    assert scipy_coo.scipy_cls_type == 'coo'

    scipy_csr = EmbeddingClsType.SCIPY_CSR
    assert not scipy_csr.is_dense
    assert not scipy_csr.is_torch
    assert not scipy_csr.is_tf
    assert scipy_csr.is_sparse
    assert scipy_csr.is_scipy
    assert scipy_csr.is_scipy_stackable
    assert scipy_csr.scipy_cls_type == 'csr'

    scipy_bsr = EmbeddingClsType.SCIPY_BSR
    assert not scipy_bsr.is_dense
    assert not scipy_bsr.is_torch
    assert not scipy_bsr.is_tf
    assert scipy_bsr.is_sparse
    assert scipy_bsr.is_scipy
    assert not scipy_bsr.is_scipy_stackable
    assert scipy_bsr.scipy_cls_type == 'bsr'

    scipy_csc = EmbeddingClsType.SCIPY_CSC
    assert not scipy_csc.is_dense
    assert not scipy_csc.is_torch
    assert not scipy_csc.is_tf
    assert scipy_csc.is_sparse
    assert scipy_csc.is_scipy
    assert not scipy_csc.is_scipy_stackable
    assert scipy_csc.scipy_cls_type == 'csc'

    torch = EmbeddingClsType.TORCH
    assert torch.is_sparse
    assert torch.is_torch
    assert not torch.is_scipy
    assert not torch.is_dense
    assert not torch.is_scipy_stackable
    assert not torch.is_tf
    assert torch.scipy_cls_type is None

    tf = EmbeddingClsType.TF
    assert tf.is_sparse
    assert tf.is_tf
    assert not tf.is_scipy
    assert not tf.is_dense
    assert not tf.is_scipy_stackable
    assert not tf.is_torch
    assert tf.scipy_cls_type is None
