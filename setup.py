#!/usr/bin/env python

from setuptools import setup,find_packages
from os import mkdir
from pathlib import Path

import sys
sys.path.append('.')

home = Path.home()

# Configure CloudMeasurementDirectory
cm_path = home / ".CloudMeasurement"
cm_path.mkdir(exist_ok=True)

cli = Path('bin/cm')
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
    install_requires=['setuptools', 'awscli'],
    entry_points={"console_scripts": ["cm = bin.cm:main"]},
    zip_safe=False
)
