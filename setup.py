#!/usr/bin/env python

import setuptools

setuptools.setup(
    name='pint-proj',
    version='0.0.1',
    description='Pint support for geographic coordinates, map projections and chart datums',
    long_description='''Representations for geographic coordinates and transforms for reprojecting
coordinates and calculating distances.''',
    long_description_content_type="text/markdown",
    author='Egil Moeller',
    author_email='redhog@redhog.org',
    url='https://github.com/redhog/pint-proj',
    packages=setuptools.find_packages(),
    install_requires=[
        "pandas",
        "pint",
        "pint-pandas",
        "pyproj",
        "projnames",
    ]
)

