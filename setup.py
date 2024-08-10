import re
from setuptools import setup


def get_long_description():
    with open('README.md', 'r') as fh:
        return fh.read()


def get_version():
    init_file = 'path4gmns/__init__.py'
    with open(init_file, 'r') as fh:
        content = fh.read()

    version = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", content, re.M)
    if version:
        return version.group(1)

    raise RuntimeError('unable to find version info in __init__.py')


setup(
    name="path4gmns",
    version=get_version(),
    author="Dr. Xuesong Zhou, Dr. Peiheng Li",
    author_email="xzhou74@asu.edu, jdlph@hotmail.com",
    description="An open-source, cross-platform, lightweight, and fast Python\
                path engine for networks encoded in GMNS",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/jdlph/PATH4GMNS",
    packages=['path4gmns'],
    package_dir={'path4gmns': 'path4gmns'},
    package_data={'path4gmns': ['bin/*']},
    license='Apache License 2.0',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)