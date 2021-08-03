import pytest
import numpy as np


@pytest.fixture
def embeddings():
    return np.array([[1, 0, 0], [2, 0, 0], [3, 0, 0]])


@pytest.fixture
def embedding_query():
    return np.array([[1, 0, 0]])


@pytest.fixture
def other_embeddings():
    return np.array([[2, 0, 0], [3, 0, 0]])
