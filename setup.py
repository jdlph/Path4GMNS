import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="path4gmns", 
    version="0.5.3",
    author="Dr. Xuesong Zhou, Dr. Peiheng Li",
    author_email="xzhou74@asu.edu, jdlph@hotmail.com",
    description="an open-source, cross-platform, lightweight, and fast Python\
                path engine for networks encoded in GMNS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jdlph/PATH4GMNS",
    packages=['path4gmns'],
    package_dir={'path4gmns': 'path4gmns'},
    package_data={'path4gmns': ['bin/*']},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
