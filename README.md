# PyApacheAtlas

A python package to work with the Apache Atlas API and support bulk loading from different file types.

The package currently supports:
* Bulk upload of entities.
* Bulk upload of type definitions.
* Creating custom lineage between two existing entities.
* Creating custom table and complex column level lineage in the [Hive Bridge style](https://atlas.apache.org/0.8.3/Bridge-Hive.html).
  * Supports Azure Data Catalog ColumnMapping Attributes.
* Creating a column lineage scaffolding as in the Hive Bridge Style .
* Performing "What-If" analysis to check if...
   * Your entities are valid types.
   * Your entities are missing required attributes.
   * Your entities are using undefined attributes.
* Working with the glossary.
  * Uploading terms.
  * Downloading individual or all terms.
* Working with relationships.
  * Able to create arbitrary relationships between entities.
  * e.g. associating a given column with a table.
  * Able to upload relationship definitions.
* Deleting types (by name) or entities (by guid).
* Search (only for Azure Data Catalog advanced search).
* Authentication to Azure Data Catalog via Service Principal.
* Authentication using basic authentication of username and password for open source Atlas.

## Quickstart

### Build and Install from Source

Create a wheel distribution file and install it in your environment.

```
python -m pip install wheel
python setup.py bdist_wheel
python -m pip install ./dist/pyapacheatlas-0.0b19-py3-none-any.whl
```

### Create a Client Connection

Provides connectivity to your Atlas / Data Catalog service. 
Supports getting and uploading entities and type defs.

```
from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatalas.core import AtlasClient

auth = ServicePrincipalAuthentication(
    tenant_id = "", 
    client_id = "", 
    client_secret = ""
)

# Azure Data Catalog Endpoints are:
# https://{your_catalog_name}.catalog.babylon.azure.com/api/atlas/v2

client = AtlasClient(
    endpoint_url = "https://MYENDPOINT/api/atlas/v2",
    auth = auth
)
```

### Create Entities "By Hand"

You can also create your own entities by hand with the helper `AtlasEntity` class.  Convert it with `to_json` to prepare it for upload.

```
from pyapacheatalas.core import AtlasEntity

# Get All Type Defs
all_type_defs = client.get_all_typedefs()

# Get Specific Entities
list_of_entities = client.get_entity(guid=["abc-123-def","ghi-456-jkl"])

# Create a new entity
ae = AtlasEntity(
    name = "my table", 
    typeName = "demo_table", 
    qualified_name = "somedb.schema.mytable",
    guid = -1000
)

# Upload that entity with the client
upload_results = client.upload_entities([ae.to_json()])
```

### Create Entities from Excel

Read from a standardized excel template that supports...

* Bulk uploading entities into your data catalog.
* Creating custom table and column level lineage.
* Creating custom type definitions for datasets
* Creating custom lineage between existing assets / entities in your data catalog.

See end to end samples for each scenario in the [excel samples](./samples/excel/README.md).

Learn more about the Excel [features and configuration in the wiki](https://github.com/wjohnson/pyapacheatlas/wiki/Excel-Template-and-Configuration).

## Additional Resources

* Learn more about this package in the [github wiki](https://github.com/wjohnson/pyapacheatlas/wiki/Excel-Template-and-Configuration).
* The [Apache Atlas client in Python](https://pypi.org/project/pyatlasclient/)
* The [Apache Atlas REST API](http://atlas.apache.org/api/v2/)
