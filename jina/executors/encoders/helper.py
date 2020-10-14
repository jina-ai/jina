__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np


def reduce_mean(data: 'np.ndarray', mask_2d: 'np.ndarray') -> 'np.ndarray':
    emb_dim = data.shape[2]
    mask = np.tile(mask_2d, (emb_dim, 1, 1))
    mask = np.rollaxis(mask, 0, 3)
    output = mask * data
    return np.sum(output, axis=1) / np.sum(mask, axis=1)


def reduce_max(data: 'np.ndarray', mask_2d: 'np.ndarray') -> 'np.ndarray':
    emb_dim = data.shape[2]
    mask = np.tile(mask_2d, (emb_dim, 1, 1))
    mask = np.rollaxis(mask, 0, 3)
    output = mask * data
    neg_mask = (mask_2d - 1) * 1e10
    neg_mask = np.tile(neg_mask, (emb_dim, 1, 1))
    neg_mask = np.rollaxis(neg_mask, 0, 3)
    output += neg_mask
    return np.max(output, axis=1)


def reduce_min(data: 'np.ndarray', mask_2d: 'np.ndarray') -> 'np.ndarray':
    emb_dim = data.shape[2]
    mask = np.tile(mask_2d, (emb_dim, 1, 1))
    mask = np.rollaxis(mask, 0, 3)
    output = mask * data
    neg_mask = (mask_2d - 1) * (-1e10)
    neg_mask = np.tile(neg_mask, (emb_dim, 1, 1))
    neg_mask = np.rollaxis(neg_mask, 0, 3)
    output += neg_mask
    return np.min(output, axis=1)


def reduce_cls(data: 'np.ndarray', mask_2d: 'np.ndarray', cls_pos: str = 'head') -> 'np.ndarray':
    mask_pruned = prune_mask(mask_2d, cls_pos)
    return reduce_mean(data, mask_pruned)


def prune_mask(mask: 'np.ndarray', cls_pos: str='head') -> 'np.ndarray':
    result = np.zeros(mask.shape)
    if cls_pos == 'head':
        mask_row = np.zeros((1, mask.shape[1]))
        mask_row[0, 0] = 1
        result = np.tile(mask_row, (mask.shape[0], 1))
    elif cls_pos == 'tail':
        for row_index, num_tokens in enumerate(np.sum(mask, axis=1).tolist()):
            result[row_index, int(num_tokens) - 1] = 1
    else:
        raise NotImplementedError
    return result
