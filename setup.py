#!/usr/bin/env python
# Copyright 2010 Greplin, Inc.  All Rights Reserved.

"""Setup script for Tornado compatible API for Stripe."""


try:
  from setuptools import setup
except ImportError:
  from distutils.core import setup


setup(name='stripe-tornado',
      version='1.4.3',
      description='Stripe tornado python bindings',
      license='Apache',
      author='Greplin, Inc.',
      author_email='opensource@greplin.com',
      url='http://www.github.com/Greplin/stripe-tornado',
      packages=['stripe'],
      package_dir = {'' : 'src'}
)

