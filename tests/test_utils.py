import numpy as np
import pytest
from merge.utils import (
    parse_slice, get_range, group_files, items_to_merge, save, load)


@pytest.mark.parametrize(
    "str, expected", [
        (":", slice(None)),
        ("5:", slice(5, None)),
        (":5", slice(None, 5)),
        ("3:5", slice(3, 5)),
        ("::2", slice(None, None, 2)),
        (":5:", slice(None, 5)),
        ("5::", slice(5, None)),
        ("1:3:5", slice(1, 3, 5))
    ])
def test_parse_slice(str, expected):
    assert parse_slice(str) == expected


@pytest.mark.parametrize(
    "first, last, s, expected", [
        (1, 9, slice(3, 7), range(3, 7)),
        (4, 9, slice(3, 7), range(4, 7)),
        (1, 5, slice(3, 7), range(3, 6)),
        (4, 5, slice(3, 7), range(4, 6))
    ])
def test_get_range(first, last, s, expected):
    r = get_range(first, last, s)
    assert r == expected


def test_get_range_negative_step():
    with pytest.raises(ValueError):
        get_range(1, 4, slice(3, 1, -1))


files = [
    "a-0.tif", "a-1.tif", "a-3.tif", "b-1.tif", "b-2.tif", "c_0.tif", "d-1.log"
]


def test_group_files():
    grouped = group_files(files)
    assert grouped == {
        "a": [(0, "a-0.tif"), (1, "a-1.tif"), (3, "a-3.tif")],
        "b": [(1, "b-1.tif"), (2, "b-2.tif")]
    }


def test_items_to_merge_order():
    names = ["a", "b", "c", "d", "e"]
    files = ["{}-0.tif".format(name) for name in names]
    grouped = group_files(files)
    assert list(grouped.keys()) == names


def test_items_to_merge_missing():
    items = group_files(files)["a"]
    sliced, missing, dups = items_to_merge(items)
    assert sliced == [(0, "a-0.tif"), (1, "a-1.tif"), (3, "a-3.tif")]
    assert missing == [2]
    assert dups == []


def test_items_to_merge_duplicates():
    files_with_dups = files.copy()
    files_with_dups.insert(0, "a-00.tif")
    files_with_dups.append("a-01.tif")
    files_with_dups.append("a-001.tif")
    items = group_files(files_with_dups)["a"]
    sliced, missing, dups = items_to_merge(items)
    assert sliced == [(0, "a-00.tif"), (1, "a-1.tif"), (3, "a-3.tif")]
    assert missing == [2]
    assert dups == [0, 1]


def test_items_to_merge_slice():
    items = group_files(files)["a"]
    sliced, missing, dups = items_to_merge(items, slice(1, 2))
    assert sliced == [(1, "a-1.tif")]
    assert missing == []
    assert dups == []


def test_items_to_merge_missing_front():
    items = group_files(files)["b"]
    sliced, missing, dups = items_to_merge(items)
    assert sliced == [(1, "b-1.tif"), (2, "b-2.tif")]
    assert missing == []
    assert dups == []


def test_items_to_merge_step():
    items = group_files(files)["a"]
    sliced, missing, dups = items_to_merge(items, slice(1, None, 2))
    assert sliced == [(1, "a-1.tif"), (3, "a-3.tif")]
    assert missing == []
    assert dups == []


def test_items_to_merge_exclude():
    items = group_files(files)["a"]
    sliced, missing, dups = items_to_merge(items, slice(1, 3), exclude=[2])
    assert sliced == [(1, "a-1.tif")]
    assert missing == []
    assert dups == []


def test_save_load(tmp_path):
    image = np.random.randint(2**32, size=(100, 200), dtype="uint32")
    filename = tmp_path / "test.tif"
    save(filename, image)
    assert np.allclose(load(filename), image)
