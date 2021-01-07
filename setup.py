import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="path4gmns", 
    version="0.0.1",
    author="Dr.Xuesong Zhou, Dr. Peiheng Li",
    author_email="Xuesong.Zhou@asu.edu, jdlph@hotmail.com",
    description="demo",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jdlph/PATH4GMNS",
    packages=['path4gmns'],
    data_files=[('bin', ['./bin/libstalite.dll'])],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3.0",
        "Operating System :: OS Independent",
    ],
)