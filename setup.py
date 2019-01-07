#!/usr/bin/env python
# coding: utf-8

from setuptools import setup

long_description = '''
# What's FlashOps

FlashOps (a clipped compound of "flash" and "operations") is a tool that simplifies the process of managing a Linux server through SSH. A set of operations or commands that you often perform can be simplified to just one or two characters.

Maybe you think a shell script is good way to do your work. But FlashOps can do more, like sync file between remote and your computer.

# How to use

FlashOps uses Fabric to manage remote Linux servers via SSH. Before using FlashOps, make sure you can connect and manage your Linux server via SSH.

More information on [GitHub](https://github.com/dongyg/flashops).
'''

setup(
    name='flashops',
    version='19.01.05',
    author='dongyg',
    author_email='mikedong927@gmail.com',
    url='https://github.com/dongyg',
    license="MIT",
    description='Simplify Linux Server Operations and Maintenance',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['flashops'],
    install_requires=['fabric','pyperclip','PyYAML','six'],
    entry_points={
        'console_scripts': [
            'flashops=flashops:flashops'
        ]
    },
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ]
)