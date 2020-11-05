# PyApacheAtlas

A python package to work with the Apache Atlas API and support bulk loading from different file types.

The package currently supports:
* Creating a column lineage scaffolding as in the [Hive Bridge style](https://atlas.apache.org/0.8.3/Bridge-Hive.html).
* Creating and reading from an excel template file
* From Excel, constructing the defined entities and column lineages.
   * Table entities
   * Column entities
   * Table lineage processes
   * Column lineage processes
* Supports Azure Data Catalog ColumnMapping Attributes.
* Performing "What-If" analysis to check if...
   * Your entities are valid types.
   * Your entities are missing required attributes.
   * Your entities are using undefined attributes.
* Authentication to Azure Data Catalog via Service Principal.
* Authentication using basic authentication of username and password.

## Quickstart

### Build and Install from Source

Create a wheel distribution file and install it in your environment.

```
python -m pip install wheel
python setup.py bdist_wheel
python -m pip install ./dist/pyapacheatlas-0.0b18-py3-none-any.whl
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

Read from a standardized excel template to create table, column, table process, and column lineage entities.  Follows / Requires the hive bridge style of column lineages.

```
from pyapacheatlas.core import TypeCategory
from pyapacheatlas.scaffolding import column_lineage_scaffold
from pyapacheatlas.readers import ExcelConfiguration, ExcelReader

file_path = "./atlas_excel_template.xlsx"
# Create the Excel Template
ExcelReader.make_template(file_path)

# Populate the excel file manually!

# Generate the base atlas type defs
all_type_defs = client.get_typedefs(TypeCategory.ENTITY)

# Create objects for 
ec = ExcelConfiguration()
excel_reader = ExcelReader(ec)
# Read from excel file and convert to 
entities = excel_reader.parse_lineage(file_path, all_type_defs)

upload_results = client.upload_entities(entities)

print(json.dumps(upload,results,indent=1))
```

## Additional Resources

* Learn more about this package in the github wiki.
* The [Apache Atlas client in Python](https://pypi.org/project/pyatlasclient/)
* The [Apache Atlas REST API](http://atlas.apache.org/api/v2/)
