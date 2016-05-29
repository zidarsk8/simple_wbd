#!/usr/bin/env python3

"""Simplo wbd setup file.

This is the main setup for simple wbd. To manually install this module run:

    $ pip install .

For development to keep track of the changes in the module and to include
development and test dependecies run:

    $ pip install --editable .[dev,test]
"""

from setuptools import setup


def get_description():
    with open("README.rst") as f:
        return f.read()


if __name__ == "__main__":
    setup(
        name="simple_wbd",
        version="0.1.0",
        license="MIT",
        author="Miha Zidar",
        author_email="zidarsk8@gmail.com",
        description=("A simple python interface for World Bank Data Indicator "
                     "and Climate APIs"),
        long_description=get_description(),
        url="https://github.com/zidarsk8/simple_wbd",
        packages=["simple_wbd"],
        provides=["simple_wbd"],
        install_requires=[],
        extras_require={
            "dev": ["pylint"],
            "test": [
                "coverage",
                "codecov",
                "nose",
            ],
        },
        test_suite="tests",
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Environment :: Console",
            "Intended Audience :: Developers",
            "Intended Audience :: Science/Research",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3",
            "Topic :: Scientific/Engineering",
        ],
    )