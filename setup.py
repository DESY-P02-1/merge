#!/usr/bin/python3

import io
import os

from setuptools import setup, find_packages

# Package meta-data.
NAME = "merge"
DESCRIPTION = "Calculate reduced statistics over multiple images"
URL = "https://github.com/DESY-P02-1/merge"
EMAIL = "tim.schoof@desy.de"
AUTHOR = "Tim Schoof"
REQUIRES_PYTHON = ">=3.5.0"
VERSION = None  # Will be read from the __version__.py file

# What packages are required for this module to be executed?
REQUIRED = ["numpy", "scikit-image"]

# What packages are optional?
EXTRAS = {
    # 'fancy feature': ['django'],
}


# The rest you shouldn't have to touch too much :)
# ------------------------------------------------

here = os.path.abspath(os.path.dirname(__file__))


# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with io.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
        long_description = "\n" + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION


# Load the package's __version__.py module as a dictionary.
about = {}
if not VERSION:
    with open(os.path.join(here, "src", NAME, "__version__.py")) as f:
        exec(f.read(), about)
else:
    about["__version__"] = VERSION


# Where the magic happens:
setup(
    name=NAME,
    version=about["__version__"],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages("src", exclude=("tests",)),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": ["merge=merge.app:main"],
    },
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license="MIT",
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: Implementation :: CPython",
        "Development Status :: 3 - Alpha",
    ],
)
