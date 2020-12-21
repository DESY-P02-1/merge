"""
    A skeleton python script
"""
import sys
import argparse
from pathlib import Path
import logging
import re
from merge.accumulate import Accumulator
from merge.utils import (
    parse_slice, parse_exclude, group_files, items_to_merge, load, save)


log = logging.getLogger(__name__)


def create_parser():
    parser = argparse.ArgumentParser(
        description='Calculate reduced statistics over multiple images.')
    parser.add_argument(
        'basename', type=str, nargs='*',
        help='Basename part of filenames to merge.')
    parser.add_argument(
        '--sep', type=str, default='-',
        help='Separator between basename and index (default: "-")')
    parser.add_argument(
        '--ext', type=str, default='tif',
        help='Filename extension (default: "tif")')
    parser.add_argument(
        '--all', action='store_true',
        help='Same as basename=".*" without escaping')
    parser.add_argument(
        '--pattern', type=str,
        default=r'(?P<basename>{basename}){sep}(?P<index>[0-9]+)\.{ext}$',
        help=(
            'Full filename regex (default:'
            ' "(?P<basename>{basename}){sep}(?P<index>[0-9]+)\\.{ext}$")'))
    parser.add_argument(
        '--slice', type=str, default=':',
        help=(
            'Slice of the indices to merge in Python-notation, i.e.,'
            ' "start:stop:step", where the endpoint "stop" is *not* included'
            ' (default: ":")'))
    parser.add_argument(
        '--exclude', '-e', type=str, default='',
        help='Comma-separated list of indices to exclude (default: "")')
    parser.add_argument(
        '--dir', '-d', type=str, default='.',
        help='Root directory for data to load (default: ".")')
    parser.add_argument(
        '--avg', type=str, default='{basename}_avg_{start}_{stop}.tif',
        help=(
            'Filename for saving the average'
            ' (default: "{basename}_avg_{start}_{stop}.tif")'))
    parser.add_argument(
        '--sum', type=str, default='{basename}_sum_{start}_{stop}.tif',
        help=(
            'Filename for saving the sum'
            ' (default: "{basename}_sum_{start}_{stop}.tif")'))
    parser.add_argument(
        '--quiet', '-q', action='count', default=0, help=(
            'Reduce verbosity (can be given multiple times)'))
    parser.add_argument(
        '--log', type=str, help='Write logs to a file with the given name')

    return parser


def parse_config(args):
    if args.quiet == 0:
        level = logging.INFO
    elif args.quiet == 1:
        level = logging.WARNING
    else:
        level = logging.ERROR

    logger = logging.getLogger("merge")
    logger.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_formatter = logging.Formatter('%(levelname)-8s %(message)s')
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)

    if args.log:
        file_handler = logging.FileHandler(args.log)
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    slice = parse_slice(args.slice)
    exclude = parse_exclude(args.exclude)
    if args.all:
        if args.basename:
            log.warning("Ignoring positional arguments because --all is given")
        basenames = [".*"]
    else:
        basenames = [re.escape(basename) for basename in args.basename]
    if not basenames:
        raise ValueError("Neither basename nor --all given")
    pattern = args.pattern.format(
        basename="|".join(basenames), sep=args.sep, ext=args.ext)

    return dict(
        pattern=pattern,
        dir=args.dir,
        slice=slice,
        exclude=exclude,
        avg_pattern=args.avg,
        sum_pattern=args.sum)


def merge_items(items, accumulator):
    for index, path in items:
        try:
            value = load(path)
        except OSError:
            log.error("Cannot open '%s'", path)
        except ValueError:
            log.error("Format of '%s' not supported", path)

        accumulator(value)


def check_start(items, slice, exclude):
    first_index = items[0][0]
    if slice.start is not None:
        missing = range(first_index, slice.start)
        for i in missing:
            if i not in exclude:
                log.warning(
                    "Starting at index %d although index %d was requested",
                    first_index, i)
                return first_index

    log.info("Starting at index %d", first_index)
    return first_index


def check_stop(items, slice, exclude):
    last_index = items[-1][0]
    # It is normal Python behavior to silently accept too large endpoints
    log.info("Last index is %d", last_index)
    return last_index + 1


def check_missing(missing_indices):
    if missing_indices:
        log.warning("The following indices are missing: %s", missing_indices)


def check_duplicates(duplicated_indices):
    if duplicated_indices:
        raise ValueError(
            "There exist multiple files for the following indices: {}".format(
                duplicated_indices))


def merge_group(
        available_items, slice, exclude, basename=None, avg=None, sum=None):
    items, missing, dups = items_to_merge(available_items, slice, exclude)
    start = check_start(items, slice, exclude)
    stop = check_stop(items, slice, exclude)
    check_missing(missing)
    check_duplicates(dups)
    acc = Accumulator()
    merge_items(items, acc)
    if avg:
        avg = avg.format(basename=basename, start=start, stop=stop)
        log.info("Saving average to '%s'", avg)
        save(avg, acc.avg())
    if sum:
        sum = sum.format(basename=basename, start=start, stop=stop)
        log.info("Saving sum to '%s'", sum)
        save(sum, acc.sum())


def merge(
        pattern, dir=".", slice=slice(None), exclude=None,
        avg_pattern=None, sum_pattern=None):
    files = [file for file in Path(dir).iterdir() if file.is_file()]
    groups = group_files(files, pattern=pattern)
    for basename, available_items in sorted(groups.items()):
        log.info("Merging files for basename '%s'", basename)
        merge_group(
            available_items, slice=slice, exclude=exclude, basename=basename,
            avg=avg_pattern, sum=sum_pattern)


def main(argv=sys.argv[1:]):
    parser = create_parser()
    args = parser.parse_args(argv)
    try:
        config = parse_config(args)
    except ValueError:
        parser.print_usage()
        exit(1)

    log.debug("Using pattern '%s'", config["pattern"])
    merge(**config)

    return 0


if __name__ == "__main__":
    sys.exit(main())
