import numpy as np
import pytest
from merge.accumulate import Accumulator


def test_init():
    acc = Accumulator()
    assert acc.count() == 0
    assert acc.sum() == 0
    assert acc.avg() == 0


@pytest.mark.parametrize("value", [1, 1.5, np.arange(6).reshape((2, 3))])
def test_one(value):
    acc = Accumulator()
    ret = acc(value)
    assert ret == 1
    assert acc.count() == 1
    assert np.all(acc.sum() == value)
    assert np.all(acc.avg() == value)


@pytest.mark.parametrize(
    "values", [
        np.random.randn(10),
        np.random.randn(10, 20),
        np.random.randn(10, 20, 30)])
def test_many(values):
    acc = Accumulator()
    for i in range(values.shape[0]):
        ret = acc(values[i])
        assert ret == i + 1
    assert acc.count() == values.shape[0]
    assert np.allclose(acc.sum(), np.sum(values, axis=0))
    assert np.allclose(acc.avg(), np.mean(values, axis=0))


def test_reset():
    acc = Accumulator()
    for i in range(10):
        acc(i)
    assert acc.count() == 10
    assert acc.sum() == 45
    assert acc.avg() == 4.5

    acc.reset()
    assert acc.count() == 0
    assert acc.sum() == 0
    assert acc.avg() == 0