#!/usr/bin/python2
"""
Focus
---------


"""
from setuptools import setup, find_packages, findall


setup(
    name='Focus',
    version='1.0',
    license='Apache 2.0',
    author='Alexander Pugachev, Alessio Ababilov, Stanislav Pugachev',
    author_email='apugachev@griddynamics.com',
    description='Web interface to OpenStack',
    long_description=__doc__,
    packages=find_packages(exclude=['bin', 'tests']),
    zip_safe=False,
    platforms='any',
    scripts=findall("bin"),
    package_data = {
        "C4GD_web": [
            "../" + s
            for s in
            findall("C4GD_web/static") +
            findall("C4GD_web/templates")
        ],
    },
    install_requires=[
        'Flask',
        'Flask-WTF',
        'Jinja2',
        'MySQL-python',
        'WTForms',
        'Werkzeug',
        'Hamlish-Jinja',
        'requests',
        'gevent',
        'storm',
    ]
)
