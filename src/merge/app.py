"""
    A skeleton python script
"""
import sys
import argparse
import os
from pathlib import Path
import logging
import re
from merge.accumulate import Accumulator
from merge.utils import (
    parse_slice,
    parse_exclude,
    group_files,
    items_to_merge,
    load,
    save,
)


log = logging.getLogger(__name__)


# These defaults apply only without --verbatim and therefore cannot be set as an
# option in add_argument
SEP_DEFAULT = "-"
EXT_DEFAULT = "tif"
PATTERN_DEFAULT = r"(?P<basename>{basename}){sep}(?P<index>[0-9]+)\.{ext}$"
SLICE_DEFAULT = ":"
EXCLUDE_DEFAULT = ""
AVG_DEFAULT = "{basename}_avg_{start}_{stop}.tif"
SUM_DEFAULT = "{basename}_sum_{start}_{stop}.tif"


def create_parser():
    parser = argparse.ArgumentParser(
        description="Calculate reduced statistics over multiple images."
    )
    parser.add_argument(
        "basename", type=str, nargs="*", help="Basename part of filenames to merge."
    )
    parser.add_argument(
        "--verbatim",
        action="store_true",
        help=(
            "Treat basenames as a verbatim list of files to merge, ignoring their"
            " indices and all other files in --dir. The names of the output files"
            " must be explicitly set via --avg and/or --sum"
        ),
    )
    parser.add_argument(
        "--sep",
        type=str,
        help=f"Separator between basename and index (default: '{SEP_DEFAULT}')",
    )
    parser.add_argument(
        "--ext",
        type=str,
        help=f"Filename extension (default: '{EXT_DEFAULT}')",
    )
    parser.add_argument(
        "--all", action="store_true", help='Same as basename=".*" without escaping'
    )
    parser.add_argument(
        "--pattern",
        type=str,
        help=("Full filename regex (default: '{PATTERN_DEFAULT}')"),
    )
    parser.add_argument(
        "--slice",
        type=str,
        help=(
            "Slice of the indices to merge, i.e., 'start:stop:step', where,"
            " unlike Python, the endpoint 'stop' *is* included"
            f" (default: '{SLICE_DEFAULT}')"
        ),
    )
    parser.add_argument(
        "--exclude",
        "-e",
        type=str,
        help=(
            "Comma-separated list of indices to exclude"
            f" (default: '{EXCLUDE_DEFAULT}')"
        ),
    )
    parser.add_argument(
        "--dir",
        "-d",
        type=str,
        default=".",
        help='Root directory for data to load (default: ".")',
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default=".",
        help='Root directory where output files are written (default: ".")',
    )
    parser.add_argument(
        "--avg",
        type=str,
        help=f"Filename for saving the average (default: '{AVG_DEFAULT}')",
    )
    parser.add_argument(
        "--sum",
        type=str,
        help=f"Filename for saving the sum (default: '{SUM_DEFAULT}')",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="count",
        default=0,
        help=("Reduce verbosity (can be given multiple times)"),
    )
    parser.add_argument(
        "--log", type=str, help="Write logs to a file with the given name"
    )

    return parser


def setup_logging(args):
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
    stream_formatter = logging.Formatter("%(levelname)-8s %(message)s")
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)

    if args.log:
        file_handler = logging.FileHandler(args.log)
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)


def parse_config_verbatim(args):
    assert args.verbatim
    setup_logging(args)

    if args.sep:
        log.warning("Ignoring --sep because --verbatim is given")
    if args.ext:
        log.warning("Ignoring --ext because --verbatim is given")
    if args.all:
        log.warning("Ignoring --all because --verbatim is given")
    if args.pattern:
        log.warning("Ignoring --pattern because --verbatim is given")
    if args.slice:
        log.warning("Ignoring --slice because --verbatim is given")
    if args.exclude:
        log.warning("Ignoring --exclude because --verbatim is given")

    filenames = [os.path.join(args.dir, filename) for filename in args.basename]

    if len(filenames) < 2:
        raise ValueError("With --verbatim, at least 2 filenames must be given")

    avg_filename = None
    sum_filename = None
    if args.avg:
        avg_filename = os.path.join(args.output_dir, args.avg)
    if args.sum:
        sum_filename = os.path.join(args.output_dir, args.sum)
    if avg_filename is None and sum_filename is None:
        raise ValueError(
            "With --verbatim, output filenames must be set via --avg and/or --sum"
        )

    return dict(
        filenames=filenames,
        avg_filename=avg_filename,
        sum_filename=sum_filename,
    )


def parse_config(args):
    setup_logging(args)
    slice = parse_slice(args.slice or SLICE_DEFAULT)
    exclude = parse_exclude(args.exclude or EXCLUDE_DEFAULT)
    if args.all:
        if args.basename:
            log.warning("Ignoring positional arguments because --all is given")
        basenames = [".*"]
    else:
        basenames = [re.escape(basename) for basename in args.basename]
    if not basenames:
        raise ValueError("Neither basename nor --all given")
    pattern = args.pattern or PATTERN_DEFAULT
    pattern = pattern.format(
        basename="|".join(basenames),
        sep=args.sep or SEP_DEFAULT,
        ext=args.ext or EXT_DEFAULT,
    )

    avg_pattern = os.path.join(args.output_dir, args.avg or AVG_DEFAULT)
    sum_pattern = os.path.join(args.output_dir, args.sum or SUM_DEFAULT)

    return dict(
        pattern=pattern,
        dir=args.dir,
        slice=slice,
        exclude=exclude,
        avg_pattern=avg_pattern,
        sum_pattern=sum_pattern,
    )


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
                    first_index,
                    i,
                )
                return first_index

    log.info("Starting at index %d", first_index)
    return first_index


def check_stop(items, slice, exclude):
    last_index = items[-1][0]
    # It is normal Python behavior to silently accept too large endpoints
    log.info("Last index is %d", last_index)
    return last_index


def check_missing(missing_indices):
    if missing_indices:
        log.warning("The following indices are missing: %s", missing_indices)


def check_duplicates(duplicated_indices):
    if duplicated_indices:
        raise ValueError(
            "There exist multiple files for the following indices: {}".format(
                duplicated_indices
            )
        )


def merge_group(available_items, slice, exclude, basename=None, avg=None, sum=None):
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


def create_output_dirs(avg_pattern, sum_pattern):
    avg_parent = Path(avg_pattern).parent
    sum_parent = Path(sum_pattern).parent
    log.info("Creating output directory '%s'", avg_parent)
    avg_parent.mkdir(parents=True, exist_ok=True)
    if sum_parent != avg_parent:
        log.info("Creating output directory '%s'", sum_parent)
        sum_parent.mkdir(parents=True, exist_ok=True)


def merge(
    pattern,
    dir=".",
    slice=slice(None),
    exclude=None,
    avg_pattern=None,
    sum_pattern=None,
):
    create_output_dirs(avg_pattern, sum_pattern)
    files = [file for file in Path(dir).iterdir() if file.is_file()]
    groups = group_files(files, pattern=pattern)
    if not groups:
        log.warning("No files matching '%s' found", pattern)
    for basename, available_items in sorted(groups.items()):
        log.info("Merging files for basename '%s'", basename)
        merge_group(
            available_items,
            slice=slice,
            exclude=exclude,
            basename=basename,
            avg=avg_pattern,
            sum=sum_pattern,
        )


def merge_verbatim(filenames, avg_filename, sum_filename):
    acc = Accumulator()
    merge_items(enumerate(filenames), acc)
    if avg_filename:
        log.info("Saving average to '%s'", avg_filename)
        save(avg_filename, acc.avg())
    if sum_filename:
        log.info("Saving sum to '%s'", sum_filename)
        save(sum_filename, acc.sum())


def main(argv=sys.argv[1:]):
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.verbatim:
        try:
            config = parse_config_verbatim(args)
        except ValueError as err:
            log.error(err)
            parser.print_usage()
            exit(1)
    else:
        try:
            config = parse_config(args)
        except ValueError as err:
            log.error(err)
            parser.print_usage()
            exit(1)

    if args.verbatim:
        log.debug("Merging files '%s'", config["filenames"])
        merge_verbatim(**config)
    else:
        log.debug("Using pattern '%s'", config["pattern"])
        merge(**config)

    return 0


if __name__ == "__main__":
    sys.exit(main())
