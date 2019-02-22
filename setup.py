#!/usr/bin/env python3

from setuptools import setup, find_packages
import re


with open('maiar_lib/__init__.py', 'r') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        f.read(), re.MULTILINE).group(1)


if not version:
    raise RuntimeError('Cannot find version information')


setup(name='maiar',
      version=version,
      author='David Tulga',
      author_email='david.tulga@freenome.com',
      description='Maiar packaging system',
      py_modules=['maiar_lib'],
      install_requires=['google-cloud-storage'],
      scripts=['bin/maiar', 'bin/generate_maiar_packages'],
      packages=find_packages())
