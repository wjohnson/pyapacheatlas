# PyApacheAtlas: API Support for Azure Purview and Apache Atlas

A python package to work with the Azure Purview and Apache Atlas API. Supporting bulk loading, custom lineage, and more from a Pythonic set of classes and Excel templates.

The package supports programmatic interaction and an Excel template for low-code uploads.

The Excel template provides a means to:
* Bulk upload entities
  * Supports adding glossary terms to entities.
  * Supports adding classifications to entities.
  * Supports creating relationships between entities (e.g. columns of a table).
* Creating custom lineage between two existing entities and using the Azure Purview Column Mappings / Lineage feature.
* Bulk upload of type definitions.
* Bulk upload of classification definitions (Purview Classification rules are not currently supported).
* Creating custom table and complex column level lineage in the [Hive Bridge style](https://atlas.apache.org/0.8.3/Bridge-Hive.html).
  * Supports Azure Purview ColumnMapping Attributes.

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
* Creating a column lineage scaffolding as in the Hive Bridge Style .
* Performing "What-If" analysis to check if...
   * Your entities are valid types.
   * Your entities are missing required attributes.
   * Your entities are using undefined attributes.
* Search (only for Azure Purview advanced search).
* Authentication to Azure Purview via Service Principal.
* Authentication using basic authentication of username and password for open source Atlas.

## Quickstart

### Install from PyPi

```
python -m pip install pyapacheatlas
```

### Create a Purview Client Connection

Provides connectivity to your Atlas / Azure Purview service. 
Supports getting and uploading entities and type defs.

```
from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient

auth = ServicePrincipalAuthentication(
    tenant_id = "", 
    client_id = "", 
    client_secret = ""
)

# Create a client to connect to your service.
client = PurviewClient(
    account_name = "Your-Purview-Account-Name",
    authentication = auth
)
```

For users wanting to use the `AtlasClient` and Purview, the Atlas Endpoint for
Purview is `https://{your_purview_name}.catalog.purview.azure.com/api/atlas/v2`.
The PurviewClient abstracts away having to know the endpoint url and is
the better way to use this package with Purview.

### Create Entities "By Hand"

You can also create your own entities by hand with the helper `AtlasEntity` class.

```
from pyapacheatlas.core import AtlasEntity

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
upload_results = client.upload_entities( [ae] )
```

### Create Entities from Excel

Read from a standardized excel template that supports...

* Bulk uploading entities into your data catalog.
* Creating custom table and column level lineage.
* Creating custom type definitions for datasets.
* Creating custom lineage between existing assets / entities in your data catalog.
* Creating custom classification (Purview Classification rules are not supported yet).

See end to end samples for each scenario in the [excel samples](./samples/excel/README.md).

Learn more about the Excel [features and configuration in the wiki](https://github.com/wjohnson/pyapacheatlas/wiki/Excel-Template-and-Configuration).

## Additional Resources

* Learn more about this package in the [github wiki](https://github.com/wjohnson/pyapacheatlas/wiki/Excel-Template-and-Configuration).
* The [Apache Atlas REST API](http://atlas.apache.org/api/v2/)
* The [Purview CLI Package](https://github.com/tayganr/purviewcli) provides CLI support.
* Purview [REST API Official Docs](https://docs.microsoft.com/en-us/azure/purview/tutorial-using-rest-apis)