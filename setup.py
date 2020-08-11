#!/usr/bin/env python

from setuptools import setup,find_packages
from os.path import join

import sys
sys.path.append('.')

cli = join('bin', 'cm')
setup(
    name='CloudMeasurement',
    version='1.0',
    packages=find_packages(),
    include_package_data=True,
    url='https://github.com/Giuseppe1992/CloudMeasurement.git',
    license='MIT',
    author='Giuseppe Di Lena',
    author_email='giuseppedilena92@gmail.com',
    description='Cloud Measurement tool',
    install_requires=['setuptools'],
    entry_points={"console_scripts": ["cm = bin.cm:main"]},
    zip_safe=False
)
