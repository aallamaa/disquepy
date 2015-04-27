#!/usr/bin/env python

"""
@file setup.py
@author Abdelkader ALLAM
@date 4/27/2015
@brief Setuptools configuration for disque client
"""

version = '0.1'

sdict = {
    'name' : 'disque',
    'version' : version,
    'description' : 'Python client for disque',
    'long_description' : 'Python client for Disque, an in-memory, distributed job queue',
    'url': 'http://github.com/aallamaa/disquepy/',
    'download_url' : 'http://alcove.io/disquepy.tgz',
    'author' : 'Abdelkader ALLAM',
    'author_email' : 'abdelkader.allam@gmail.com',
    'maintainer' : 'Abdelkader ALLAM',
    'maintainer_email' : 'abdelkader.allam@gmail.com',
    'keywords' : ['disque', 'in memory distributed job queue'],
    'license' : 'New BSD License',
    'packages' : ['disque'],
    'package_data' : {
        '': ['*.json'],
    },
    'classifiers' : [
       'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python'],
}

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
    
setup(**sdict)

