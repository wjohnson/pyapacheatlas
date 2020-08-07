import setuptools
from pyapacheatlas import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyapacheatlas",
    version=__version__,
    author="Will Johnson",
    author_email="will@willj.com",
    description="A package to simplify working with the Apache Atlas REST APIs and support bulk loading from files.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wjohnson/pyapacheatlas",
    packages=setuptools.find_packages(),
    install_requires=[
          'openpyxl>=3.0',
          'requests>=2.0'
      ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)