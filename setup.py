__author__ = 'jgevirtz'

from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='jfixture',
    version='0.1',
    description='A simple framework for testing with database fixtures',
    url='https://github.com/joshgev/jfixture',
    author='Joshua Gevirtz',
    author_email='joshgev@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    keywords='example mysql orm',
    packages=find_packages(),
    install_requires=['mysqlclient', 'nose', 'git+git://github.com/joshgev/simpleorm'])