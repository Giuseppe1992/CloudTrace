#!/usr/bin/env python

from setuptools import setup,find_packages
from os import mkdir
from pathlib import Path
from os import system

import sys
sys.path.append('.')

home = Path.home()

# Configure CloudMeasurementDirectory
cm_path = home / ".CloudMeasurement"
cm_path.mkdir(exist_ok=True, mode=0x777)

# Bad trick to avoid the umask value
print("I need your sudo password to put the permission in the ~/.CloudMeasurement directory")
system("sudo chmod -R 777 {}".format(cm_path))

ansible_path = cm_path / "ansible"
ansible_path.mkdir(exist_ok=True, mode=0x777)

print("I need your sudo password to put the permission in the ~/.CloudMeasurement/ansible directory")
system("sudo chmod -R 777 {}".format(ansible_path))


cli = Path('bin/cm')
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
    install_requires=['setuptools', 'awscli==1.18.116'],
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
