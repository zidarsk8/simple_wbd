**Simple World Band Data api interface**

.. image:: https://travis-ci.org/zidarsk8/simple_wbd.svg?branch=master
  :target: https://travis-ci.org/zidarsk8/simple_wbd
  :alt: Traves CI

.. image:: https://codecov.io/gh/zidarsk8/simple_wbd/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/zidarsk8/simple_wbd
  :alt: Code Coverage

.. image:: https://codeclimate.com/github/zidarsk8/simple_wbd/badges/gpa.svg
  :target: https://codeclimate.com/github/zidarsk8/simple_wbd
  :alt: Code Climate

.. image:: https://www.versioneye.com/user/projects/574b148fce8d0e004130d3c5/badge.svg?style=flat
  :target: https://www.versioneye.com/user/projects/574b148fce8d0e004130d3c5
  :alt: Dependency Status


This is a simple python interface for World Bank Data APIs. The goal of this project is to provide a user with the most basic interface, focused on the ease of use. For a more feature complete API helpers take a look at `wbpy <https://github.com/mattduck/wbpy>`_ and `wbdata <https://github.com/oliversherouse/wbdata>`_.


Installation
------------

For basic usage:

.. code:: sh

    pip instal git+git://github.com/zidarsk8/simple_wbd.git


Usage
-----

.. code:: python

    import simple_wbd
    api = simple_wbd.ClimateAPI()
    climate = api.get_instrumental("Italy")

    climates = api.get_instrumental(["Italy", "Slovenia", "US"])


For development
---------------

Install

.. code:: sh

    virtualenv --python=python3 venv3
    venv3/bin/activate
    git clone git://github.com/zidarsk8/simple_wbd.git
    cd simple_wbd
    pip install -e .[dev,test]

Run tests

.. code:: sh

    python setup.py test
