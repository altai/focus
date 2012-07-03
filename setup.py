#!/usr/bin/python2
"""
Focus
---------


"""
from setuptools import setup, find_packages, findall


setup(
    name='Focus',
    version='1.0',
    license='',
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
        'gevent==0.13.7',
        'netaddr==0.7.5',
        'pylibmc',
        'httplib2==0.7.2',
        'python-glanceclient',
        'python-keystoneclient',
        'python-novaclient',
        'requests==0.11.1',
        'storm==0.19',
        'Flask >= 0.9',
        'Flask-WTF==0.6',
        'Flask-Mail==0.6.1',
        'Flask-Principal==0.2',
        'Flask-Uploads==0.1.3',
        'Hamlish-Jinja',
        'Jinja2',
        'MySQL-python',
        'Tornado',
        'Werkzeug',
        'WTForms',
        'chardet',
        'python-openstackclient-base'
    ],
    test_suite='C4GD_web.tests'
)
