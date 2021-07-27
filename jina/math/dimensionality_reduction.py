import numpy as np


class PCA:
    """:class:`PCA` is a class for dimensionality reduction using PCA in Jina.

    :param n_components: Number of components to keep when projecting with PCA
    :param whiten: Flag variable stating if there projecting with whitening
    """

    def __init__(self, n_components: int, whiten: bool = False):
        self.n_components = n_components
        self.whiten = whiten
        self.e_values = None
        self.w = None

    def fit(self, x_mat: np.ndarray):
        """
        Computes the projection matrix of the PCA algorithm and stores it to self.w

        :param x_mat: Matrix of shape (n_observations, n_features)
        """

        x_mat = x_mat - x_mat.mean(axis=0)

        # covariance matrix (n_features, n_features)
        cov = np.cov(x_mat.T) / x_mat.shape[0]

        # Compute eigenvalues eigenvectors of cov
        e_values, e_vectors = np.linalg.eig(cov)

        # Sort eigenvalues by magnitude (higher to lower)
        idx = e_values.argsort()[::-1]
        e_values = e_values[idx]

        # Sort eigen vectors by eigenvalue magnitude (higher to lower)
        e_vectors = e_vectors[:, idx]

        # Projection matrix contains eigenvectors sorted
        self.w = e_vectors
        self.e_values = e_values

    def transform(self, x_mat: np.ndarray) -> np.ndarray:
        """Projects data from n_features to self.n_components features.

        :param x_mat: Matrix of shape (n_observations, n_features)
        :return: Matrix of shape (n_observations, self.n_components)
        """
        if self.w is not None:
            x_mat_projected = x_mat.dot(self.w[:, : self.n_components])
            if self.whiten:
                return x_mat_projected / np.sqrt(self.e_values[0 : self.n_components])
            else:
                return x_mat_projected

    def fit_transform(self, x_mat: np.ndarray) -> np.ndarray:
        """Fits the PCA and returns a transformed data
        :param x_mat:  Matrix of shape (n_observations, n_features)
        :return: Matrix of shape (n_observations, self.n_components)
        """
        self.fit(x_mat)
        return self.transform(x_mat)
