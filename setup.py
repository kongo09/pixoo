#!/usr/bin/python
"""
    Setup.py file for pixoo package
"""
from setuptools import setup

setup(
    name="pixoo",
    version="0.8.0",
    author="Ron Talman, kongo09",
    description=(
        "A library to easily communicate with the Divoom Pixoo 64",
        "(and hopefully soon more screens that support Wi-Fi)",
    ),
    license="BSD",
    keywords="pixoo",
    url="https://github.com/kongo09/pixoo#readme",
    project_urls={
        "Bug Tracker": "https://github.com/kongo09/pixoo/issues",
    },
    packages=['pixoo'],
    install_requires=[
        'requests ~= 2.31.0',
        'Pillow ~= 10.0.0',
    ],
    python_requires=">=3.10",
    package_dir={"": "."},
)
