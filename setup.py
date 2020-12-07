import setuptools
from pyapacheatlas import __version__

LONG_DESCRIPTION = """
# PyApacheAtlas: API Support for Apache Atlas and Azure Purview

A python package to work with the Apache Atlas API and support bulk loading, custom lineage, and more from a Pythonic set of classes and Excel templates. 

The package currently supports:
* Creating a column lineage scaffolding as in the [Hive Bridge style](https://atlas.apache.org/0.8.3/Bridge-Hive.html).
* Creating and reading from an excel template file
* From Excel, constructing the defined entities and column lineages.
   * Table entities
   * Column entities
   * Table lineage processes
   * Column lineage processes
* From excel, bulk uploading entities, creating / updating lineage, and creating custom types.
* Supports Azure Purview ColumnMapping attributes.
* Performing "What-If" analysis to check if...
   * Your entities are valid types.
   * Your entities are missing required attributes.
   * Your entities are using undefined attributes.
* Authentication to Azure Purview via Service Principal.
* Authentication using basic authentication of username and password.
"""

def setup_package():
    setuptools.setup(
        name="pyapacheatlas",
        version=__version__,
        author="Will Johnson",
        author_email="will@willj.com",
        description="A package to simplify working with the Apache Atlas REST APIs for Atlas and Azure Purview.",
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
        long_description=LONG_DESCRIPTION
    )

if __name__ == "__main__":
    setup_package()