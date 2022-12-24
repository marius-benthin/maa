import torch
import numpy
from sklearn.base import TransformerMixin


class Preprocessor(TransformerMixin):

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.astype(numpy.float32)
        return X


class DNN(torch.nn.Module):

    def __init__(self, D_in=None, D_out=None):
        super(DNN, self).__init__()

        self.stack = torch.nn.Sequential(
            torch.nn.Linear(D_in, 2048),
            torch.nn.ReLU(),
            torch.nn.Linear(2048, 1024),
            torch.nn.ReLU(),
            torch.nn.Dropout(p=0.5),
            torch.nn.Linear(1024, D_out),
        )

    # forward propagate input
    def forward(self, X: torch.Tensor):
        return self.stack(X)
