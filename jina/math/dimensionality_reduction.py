import numpy as np


class CustomPCA:
    """A class for PCA dimensionality reduction in Jina."""

    def __init__(self, k):
        self.k = k

    def fit(self, x_mat):
        """
        Computes the projection matrix of the PCA algorithm and stores it to self.w

        :param x_mat: Matrix of shape (n_observations, n_features)
        """
        # x_matrix.shape = (n_observations, n_features)

        x_mat = x_mat - x_mat.mean(axis=0)

        # covariance matrix (n_features, n_features)
        cov = np.cov(x_mat.T) / x_mat.shape[0]

        # Compute eigenvalues eigenvectors of cov
        e_values, e_vectors = np.linalg.eig(cov)

        # Sort eigen values by magnitude (higher to lower)
        idx = e_values.argsort()[::-1]
        e_values = e_values[idx]

        # Sort eigen vectors by eigen value magnitude (higher to lower)
        e_vectors = e_vectors[:, idx]

        # Projection matrix contains eigen vectors sorted
        self.w = e_vectors

    def transform(self, x_mat):
        """Projects data from n_features to self.k features.

        :param x_mat: Matrix of shape (n_observations, n_features)
        :return: Matrix of shape (n_observations, self.k)
        """
        return x_mat.dot(self.w[:, : self.k])
