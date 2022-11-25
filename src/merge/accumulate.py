import numpy as np


def promote_dtype(dtype):
    # TODO: Is this sufficient?
    if dtype.itemsize <= 4:
        return "float32"
    else:
        return "float64"


class Accumulator:
    def __init__(self):
        self.reset()

    def __call__(self, value):
        if self._count == 0:
            try:
                self._sum = np.zeros_like(value, dtype=promote_dtype(value.dtype))
            except AttributeError:
                # value doesn't have a dtype attribute,
                # therefore no promotion can be done
                pass
        self._sum += value
        self._count += 1
        return self._count

    def reset(self):
        self._sum = 0
        self._count = 0

    def count(self):
        return self._count

    def sum(self):
        return self._sum

    def avg(self):
        if self.count() == 0:
            return 0
        return self.sum() / self.count()
