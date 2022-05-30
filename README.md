# PyApacheAtlas: A Python SDK for Azure Purview and Apache Atlas

![PyApacheAtlas Logo](https://repository-images.githubusercontent.com/278894029/9a92fb00-37ee-11eb-8d1a-093914a7ceeb)

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

## Quickstart

### Install from PyPi

```
python -m pip install pyapacheatlas
```

### Using Azure-Identity and the Azure CLI to Connect to Purview

For connecting to Azure Purview, it's even more convenient to install the [azure-identity](https://pypi.org/project/azure-identity/) package and its support for Managed Identity, Environment Credential, and Azure CLI credential.

If you want to use your Azure CLI credential rather than a service principal, install azure-identity by running `pip install azure-identity` and then run the code below.

```python
from azure.identity import AzureCliCredential

from pyapacheatlas.core import PurviewClient

cred = AzureCliCredential()

# Create a client to connect to your service.
client = PurviewClient(
    account_name = "Your-Purview-Account-Name",
    authentication = cred
)
```

### Create a Purview Client Connection Using Service Principal

If you don't want to install any additional packages, you should use the built-in ServicePrincipalAuthentication class.

```python
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

### Create Entities "By Hand"

You can also create your own entities by hand with the helper `AtlasEntity` class.

```python
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
* Purview [REST API Official Docs](https://docs.microsoft.com/en-us/rest/api/purview/)