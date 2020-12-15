from collections import OrderedDict
from pathlib import Path
import re
from skimage.io import imread, imsave


def get_or_emplace(mapping, key, default):
    value = mapping.get(key, None)
    if value:
        return value
    else:
        mapping[key] = default
        return default


def group_files(
        files,
        pattern=r"(?P<basename>.+)-(?P<index>[0-9]+)\.tif"):
    regex = re.compile(pattern)
    ret = OrderedDict()
    for f in files:
        m = regex.match(Path(f).name)
        if m:
            key = m.group("basename")
            item = (int(m.group("index")), f)
            items = get_or_emplace(ret, key, [])
            items.append(item)

    return ret


def get_range(first, last, slice):
    start, stop, step = slice.indices(last + 1)
    if step < 0:
        raise ValueError("Negative step not allowed, got " + str(step))
    # adjust start for missing indices
    start = max(first, start)
    return range(start, stop, step)


def items_to_merge(items, slice=slice(None), exclude=[]):
    items = sorted(items)
    first_index = items[0][0]
    last_index = items[-1][0]
    indices = get_range(first_index, last_index, slice)
    sliced_items = []
    missing_indices = []
    pos = 0
    for i in indices:
        while pos < len(items) and items[pos][0] < i:
            pos += 1
        if pos < len(items) and i == items[pos][0]:
            item = items[pos]
            pos += 1
        else:
            # index is missing in items
            item = None

        if i not in exclude:
            if item:
                sliced_items.append(item)
            else:
                missing_indices.append(i)

    return sliced_items, missing_indices


def parse_slice(str):
    start, stop, *step = str.split(":")
    if start:
        start = int(start)
    else:
        start = None
    if stop:
        stop = int(stop)
    else:
        stop = None
    if step:
        if step[0]:
            step = int(step[0])
        else:
            step = None
    else:
        step = None
    return slice(start, stop, step)


def parse_exclude(str):
    if str:
        return [int(elem) for elem in str.split(",")]
    else:
        return []


def load(path):
    return imread(str(path))


def save(path, image):
    imsave(str(path), image)
