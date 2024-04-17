#!/usr/bin/env python3
import argparse
import os
import sys
import urllib.request

import numpy as np
import sklearn.base
import sklearn.linear_model
import sklearn.model_selection
import sklearn.pipeline
import sklearn.preprocessing

parser = argparse.ArgumentParser()
# These arguments will be set appropriately by ReCodEx, even if you change them.
parser.add_argument("--data_size", default=5000, type=int, help="Data size")
parser.add_argument("--max_iter", default=100, type=int, help="Maximum iterations for LR")
parser.add_argument("--pca", default=None, type=int, help="PCA dimensionality")
parser.add_argument("--recodex", default=False, action="store_true", help="Running in ReCodEx")
parser.add_argument("--seed", default=42, type=int, help="Random seed")
parser.add_argument("--solver", default="saga", type=str, help="LR solver")
parser.add_argument("--test_size", default=0.5, type=lambda x: int(x) if x.isdigit() else float(x), help="Test size")
# If you add more arguments, ReCodEx will keep them with your default values.


class MNIST:
    """MNIST Dataset.

    The train set contains 60000 images of handwritten digits. The data
    contain 28*28=784 values in the range 0-255, the targets are numbers 0-9.
    """
    def __init__(self,
                 name="mnist.train.npz",
                 data_size=None,
                 url="https://ufal.mff.cuni.cz/~courses/npfl129/2324/datasets/"):
        if not os.path.exists(name):
            print("Downloading dataset {}...".format(name), file=sys.stderr)
            urllib.request.urlretrieve(url + name, filename="{}.tmp".format(name))
            os.rename("{}.tmp".format(name), name)

        # Load the dataset, i.e., `data` and optionally `target`.
        dataset = np.load(name)
        for key, value in dataset.items():
            setattr(self, key, value[:data_size])
        self.data = self.data.reshape([-1, 28*28]).astype(float)


class PCATransformer(sklearn.base.TransformerMixin):

    NUM_ITERS = 10

    def __init__(self, n_components, seed):
        self._n_components = n_components
        self._seed = seed

    def fit(self, X, y=None):
        generator = np.random.RandomState(self._seed)

        # TODO: Compute the `self._n_components` principal components
        # and store them as columns of `self._V` matrix.
        X_mean = np.mean(X, axis=0)

        if self._n_components <= 10:
            # TODO: Use the power iteration algorithm for <= 10 dimensions.
            #
            # To compute every eigenvector, apply 10 iterations, and set
            # the initial value of every eigenvector to
            #   `generator.uniform(-1, 1, size=X.shape[1])`
            # Compute the vector norms using `np.linalg.norm`.
            S = (1 / X.shape[0]) * (X - X_mean).T @ (X - X_mean)
             # S.shape[0] == X.shape[1]
            self._V = np.zeros((S.shape[0], self._n_components))

            for i in range(self._n_components):
                v = generator.uniform(-1, 1, size=S.shape[0])
                for _ in range(self.NUM_ITERS):
                    v = S @ v
                    v_norm = np.linalg.norm(v)
                    v /= v_norm
                self._V[:, i] = v
                S -= v_norm * np.outer(v, v)
            
            # raise NotImplementedError()

        else:
            # TODO: Use the SVD decomposition computed with `np.linalg.svd`
            # to find the principal components.
            svd = np.linalg.svd(X - X_mean, compute_uv=True)
            # svd[2] is the Vh matrix
            self._V = svd[2][:self._n_components].T
            # raise NotImplementedError()

        # We round the principal components to avoid rounding errors during
        # ReCodEx evaluation.
        self._V = np.around(self._V, decimals=4)

        return self

    def transform(self, X):
        # TODO: Transform the given `X` using the precomputed `self._V`.
        return X @ self._V
        # raise NotImplementedError()


def main(args: argparse.Namespace) -> float:
    # Use the MNIST dataset.
    dataset = MNIST(data_size=args.data_size)

    # Split the dataset into a train set and a test set.
    train_data, test_data, train_target, test_target = sklearn.model_selection.train_test_split(
        dataset.data, dataset.target, test_size=args.test_size, random_state=args.seed)

    pca = [("PCA", PCATransformer(args.pca, args.seed))] if args.pca else []

    pipeline = sklearn.pipeline.Pipeline([
        ("scaling", sklearn.preprocessing.MinMaxScaler()),
        *pca,
        ("classifier", sklearn.linear_model.LogisticRegression(
            solver=args.solver, max_iter=args.max_iter, random_state=args.seed)),
    ])
    pipeline.fit(train_data, train_target)

    test_accuracy = pipeline.score(test_data, test_target)
    return test_accuracy


if __name__ == "__main__":
    args = parser.parse_args([] if "__file__" not in globals() else None)
    accuracy = main(args)
    print("Test set accuracy: {:.2f}%".format(100 * accuracy))
