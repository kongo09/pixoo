#!/usr/bin/python
"""
    Setup.py file for pixoo package
"""
from pathlib import Path
from setuptools import setup

this_directory = Path(__file__).parent
longdescription = (this_directory / "README.md").read_text()

setup(
    name="pixoo",
    version="0.8.2",
    author="Ron Talman, kongo09",
    description=(
        "A library to easily communicate with the Divoom Pixoo 64",
        "(and hopefully soon more screens that support Wi-Fi)",
    ),
    long_description=longdescription,
    long_description_content_type='text/markdown',
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
#    package_dir={"": "."},
    include_package_data=True,
)
