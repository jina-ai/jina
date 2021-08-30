import numpy as np

class LSH:
    """
    param: k: the number of hyperplanes
    param: d: the dimensionality of the random hyperplanes 
    """

    def __init__(self, k, d):
        self.k = k
        self.d = d
        self.H = np.random.normal(0, 1, (k, d))

    def hash_to_binary_code(self, U, nr_perms, nr_coordinates):
        """
        param: U: data to be distributed to bins
        param: nr_perms: how many permutations to use
        param: nr_coordinates: the prefix length in each permutation
        """
        assert self.H.shape[1] == U.shape[1]
        hashes = np.sign(self.H.dot(U.T))
        hashes = hashes.T
        print("hashes shape", hashes.shape)
        bins = [{} for _ in range(nr_perms)]
        random_seed = []
        for perm in range(nr_perms):
            s = np.random.choice(np.arange(hashes.shape[1]), size=nr_coordinates, replace=False)
            random_seed.append(s)
            for i in range(hashes.shape[0]):
                t=tuple(hashes[i][s])
                bins[perm].setdefault(t, [])
                bins[perm][t].append(i)
        return bins, random_seed


    def get_candidates_for_queries(self, Q, bins, random_seed):
        """
        param: Q: data matrix with the query vectors
        param: bins: the bins with vectors in the different permutations
        param: random_seed: the permutations, i.e. the bit positions, defined when hashing the data
        """
        assert self.H.shape[1] == Q.shape[1]
        hashes = np.sign(self.H.dot(Q.T))
        hashes = hashes.T
        candidates = {}
        for bin, s in enumerate(random_seed):
            for i in range(hashes.shape[0]):
                t=tuple(hashes[i][s])
                if t in bins[bin]:
                    candidates.setdefault(i, set())
                    candidates[i].update(bins[bin][t])
        return candidates

