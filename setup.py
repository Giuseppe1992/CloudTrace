#!/usr/bin/env python

from setuptools import setup,find_packages
from os import mkdir
from pathlib import Path
from os import system, makedirs, umask

import sys
sys.path.append('.')

home = Path.home()

# Configure CloudMeasurementDirectory
try:
    oringinal_mask = umask(0)
    print(oringinal_mask)
    cm_path = home / ".CloudMeasurement"
    ansible_path = cm_path / "ansible"
    makedirs(cm_path, exist_ok=True, mode=0o777)
    makedirs(ansible_path, exist_ok=True, mode=0o777)

finally:
    umask(oringinal_mask)


cli = Path('bin/cm')
requirements = [req.strip() for req in open("requirements.txt", "r").readlines()]
setup(
    name='CloudMeasurement',
    version='1.0.3',
    packages=find_packages(),
    include_package_data=True,
    url='https://github.com/Giuseppe1992/CloudMeasurement.git',
    license='MIT',
    long_description="TODO",
    long_description_content_type="text/plain",
    author='Giuseppe Di Lena',
    author_email='giuseppedilena92@gmail.com',
    description='Cloud Measurement tool',
    install_requires=requirements,
    entry_points={"console_scripts": ["cm = bin.cm:main"]},
    zip_safe=False,
    python_requires='>=3.6',
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 3 - Alpha",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Topic :: Software Development :: Libraries :: Application Frameworks"

    ],

)
