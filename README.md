# merge

![Build Status](https://github.com/DESY-P02-1/merge/actions/workflows/ci.yml/badge.svg?branch=master)

merge calculates reduced statistics over multiple images

> This project is in an early stage of development and should be used with caution


## Usage

For example

```
$ merge
usage: merge [-h] [--sep SEP] [--ext EXT] [--all] [--pattern PATTERN]
             [--slice SLICE] [--exclude EXCLUDE] [--dir DIR]
             [--output-dir OUTPUT_DIR] [--avg AVG] [--sum SUM] [--quiet]
             [--log LOG]
             [basename ...]
...
$ merge --slice 5:8 --avg averaged.tif --sum summed.tif basename
```

The above will calculate the average and sum of the files `basename-5.tif`,
`basename-6.tif`, `basename-7.tif`, and `basename-8.tif` (note that the endpoint
*is* included in the slice) and save them in `averaged.tif` and `summed.tif`,
respectively.

See full help message for details.

## Installation

merge requires

* python >= 3.6
* numpy
* scikit-image

Download the latest release and extract it. Optionally run

```
$ cd merge
$ python3 -m pip install .
```


## Contribution

Please feel free to open issues or pull requests.
