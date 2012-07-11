#!/usr/bin/python2
"""
Focus
---------


"""
import os
from setuptools import setup, find_packages, findall


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='Focus',
    version='1.0',
    license='GNU LGPL 2.1',
    author='Alexander Pugachev, Alessio Ababilov, Stanislav Pugachev',
    author_email='apugachev@griddynamics.com',
    description='Web interface to OpenStack',
    long_description=__doc__,
    packages=find_packages(exclude=['bin', 'tests']),
    zip_safe=False,
    platforms='any',
    scripts=findall("bin"),
    package_data = {
        "focus": [
            "../" + s
            for s in
            findall("focus/static") +
            findall("focus/templates")
        ],
    },
    install_requires=read('requirements.txt'),
    test_suite='focus.tests'
)
