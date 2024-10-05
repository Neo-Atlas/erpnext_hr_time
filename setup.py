from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

# get version from __version__ variable in hr_time/__init__.py
from hr_time import __version__ as version

setup(
    name="hr_time",
    version=version,
    description="Time management module for HR",
    author="AtlasAero GmbH",
    author_email="info@atlasaero.eu",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires
)
