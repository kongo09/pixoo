#!/usr/bin/python
"""
    Setup.py file for pixoo-ng package
"""
from pathlib import Path
from setuptools import setup

this_directory = Path(__file__).parent
longdescription = (this_directory / "README.md").read_text()

setup(
    name="pixoo-ng",
    version="1.0.0",
    author="kongo09",
    description=(
        "A library to easily communicate with the Divoom Pixoo 64",
        "(and hopefully soon more screens that support Wi-Fi)",
    ),
    long_description=longdescription,
    long_description_content_type='text/markdown',
    license="Apache2.0",
    keywords="pixoo",
    url="https://github.com/kongo09/pixoo-ng#readme",
    project_urls={
        "Bug Tracker": "https://github.com/kongo09/pixoo-ng/issues",
    },
    packages=['pixoo-ng'],
    install_requires=[
        'requests ~= 2.31.0',
        'Pillow ~= 10.0.0',
    ],
    python_requires=">=3.10",
#    package_dir={"": "."},
    include_package_data=True,
)
