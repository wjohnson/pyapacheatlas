import setuptools
from pyapacheatlas import __version__

LONG_DESCRIPTION = """
# PyApacheAtlas: A Python SDK for Azure Purview and Apache Atlas

PyApacheAtlas lets you work with the Azure Purview and Apache Atlas APIs in a Pythonic way. Supporting bulk loading, custom lineage, custom type definition and more from an SDK and Excel templates / integration.

The package supports programmatic interaction and an Excel template for low-code uploads.

## Using Excel to Accelerate Metadata Uploads

* Bulk upload entities.
  * Upload entities / assets for built-in or custom types.
  * Supports adding glossary terms to entities.
  * Supports adding classifications to entities.
  * Supports creating relationships between entities (e.g. columns of a table).
* Creating custom lineage between existing entities.
* Defining Purview Column Mappings / Column Lineage.
* Bulk upload custom type definitions.
* Bulk upload of classification definitions (Purview Classification Rules not supported).

## Using the Pythonic SDK for Purview and Atlas

The PyApacheAtlas package itself supports those operations and more for the advanced user:
* Programmatically create Entities, Types (Entity, Relationship, etc.).
* Perform partial updates of an entity (for non-complex attributes like strings or integers).
* Extracting entities by guid or qualified name.
* Creating custom lineage with Process and Entity types.
* Working with the glossary.
  * Uploading terms.
  * Downloading individual or all terms.
* Working with classifications.
  * Classify one entity with multiple classifications.
  * Classify multiple entities with a single classification.
  * Remove classification ("declassify") from an entity.
* Working with relationships.
  * Able to create arbitrary relationships between entities.
  * e.g. associating a given column with a table.
* Deleting types (by name) or entities (by guid).
* Performing "What-If" analysis to check if...
   * Your entities are valid types.
   * Your entities are missing required attributes.
   * Your entities are using undefined attributes.
* Azure Purview's Search: query, autocomplete, suggest, browse.
* Authentication to Azure Purview using azure-identity and Service Principal
* Authentication to Apache Atlas using basic authentication of username and password.
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
        long_description=LONG_DESCRIPTION,
        options={'console_scripts':{"pyapacheatlas":"pyapacheatlas:main"}}
    )

if __name__ == "__main__":
    setup_package()