from merge.app import create_parser, parse_config, merge_group, main
from merge.utils import load, save
import numpy as np
import pytest


def test_parse_config_escape():
    args = create_parser().parse_args(["foo(bar)"])
    config = parse_config(args)
    expected = r"(?P<basename>foo\(bar\))-(?P<index>[0-9]+)\.tif$"
    assert config["pattern"] == expected


def test_parse_config_sep():
    args = create_parser().parse_args(["--sep", "_", "foo"])
    config = parse_config(args)
    expected = r"(?P<basename>foo)_(?P<index>[0-9]+)\.tif$"
    assert config["pattern"] == expected


def test_parse_config_ext():
    args = create_parser().parse_args(["--ext", "cbf", "foo"])
    config = parse_config(args)
    expected = r"(?P<basename>foo)-(?P<index>[0-9]+)\.cbf$"
    assert config["pattern"] == expected


def test_parse_config_all():
    args = create_parser().parse_args(["--all"])
    config = parse_config(args)
    expected = r"(?P<basename>.*)-(?P<index>[0-9]+)\.tif$"
    assert config["pattern"] == expected


def test_parse_config_multiple_basenames():
    args = create_parser().parse_args(["foo", "bar"])
    config = parse_config(args)
    expected = r"(?P<basename>foo|bar)-(?P<index>[0-9]+)\.tif$"
    assert config["pattern"] == expected


def test_parse_config_basename_and_all(caplog):
    args = create_parser().parse_args(["--all", "bar"])
    config = parse_config(args)
    expected = r"(?P<basename>.*)-(?P<index>[0-9]+)\.tif$"
    assert config["pattern"] == expected
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "WARNING"


def test_merge_group_duplicates():
    items = [(1, "a-1.tif"), (2, "a-2.tif"), (2, "a-02.tif")]
    with pytest.raises(ValueError):
        merge_group(items, slice(None), [])


files = [
    "a-0.tif", "a-0.tif.metadata", "a-1.tif", "a-3.tif", "b-1.tif", "b-2.tif",
    "c_0.tif", "d-1.log"
]


def test_main(tmp_path):
    images = {}
    for file in files:
        key = file[0]
        ext = file[-3:]
        if ext != "tif":
            (tmp_path / file).write_text("some text")
            continue

        image = np.random.randint(2**32, size=(10, 20), dtype="uint32")

        if key in images:
            images[key].append(image)
        else:
            images[key] = [image]

        save(tmp_path / file, image)

    main([
        "--all", "--slice", ":1", "--dir", str(tmp_path),
        "--avg", str(tmp_path / "{basename}_avg_{start}_{stop}.tif"),
        "--sum", str(tmp_path / "{basename}_sum_{start}_{stop}.tif")])

    avg_a = tmp_path / "a_avg_0_1.tif"
    sum_a = tmp_path / "a_sum_0_1.tif"
    avg_b = tmp_path / "b_avg_1_1.tif"
    sum_b = tmp_path / "b_sum_1_1.tif"

    assert avg_a.is_file()
    assert sum_a.is_file()
    assert avg_b.is_file()
    assert sum_b.is_file()

    actual = load(avg_a)
    expected = np.mean(images["a"][:2], axis=0)
    assert np.allclose(actual, expected)

    actual = load(sum_a)
    expected = np.sum(images["a"][:2], axis=0)
    assert np.allclose(actual, expected)

    actual = load(avg_b)
    expected = np.mean(images["b"][:1], axis=0)
    assert np.allclose(actual, expected)

    actual = load(sum_b)
    expected = np.mean(images["b"][:1], axis=0)
    assert np.allclose(actual, expected)


def test_main_no_files(tmp_path, caplog):
    main(["--dir", str(tmp_path), "empty"])
    assert "No files matching" in caplog.text
