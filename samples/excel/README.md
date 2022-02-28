# Excel Samples for PyApacheAtlas

There are four key features of the PyApacheAtlas package with respect to the Excel frontend.

## Features and Samples
* **Generate the Excel Template**
  * After installing the PyApacheAtlas package, you can run the following code to generate an xlsx file with the latest template tabs.
  
  ```python
  from pyapacheatlas.readers import ExcelReader

  ExcelReader.make_template("./my_file_path.xlsx")

  ```
  * The below samples all create their own template file and fill it with demo data.
  * Look for the "ACTUAL WORK" comments to see what code you'd run if you filled in   the spreadsheet yourself.
  * Each tab has its own `parse_*` function in the `ExcelReader` class.

  ```python
  from pyapacheatlas.readers import ExcelReader, ExcelConfiguration

  ec = ExcelConfiguration() # Supports customization of tab names and header prefixes
  reader = ExcelReader(ec)

  file_path = 'some.xlsx'
  # Create entities (most common thing you'll do)
  reader.parse_parse_bulk_entities(file_path)
  # Connect entities / assets with custom lineage
  reader.parse_update_lineage(file_path)
  # For Azure Purview users, pdate existing process entities with column mappings
  reader.parse_column_mapping(file_path)
  # For Azure Purview users, create custom lineage with column mappings at the same time
  reader.parse_update_lineage_with_mappings(file_path)

  # Create entity type definitions
  reader.parse_entity_defs(file_path)
  # Create classification type definitions  
  reader.parse_classification_defs(file_path)

  # Create table level lineage
  reader.parse_table_lineage(file_path)
  # Create advanced column level lineage that supports fine grain attributes on the transformation
  # Requires using the column_lineage_scaffold() types
  reader.parse_finegrain_column_lineage(file_path)
  # Parse table and finegrain column lineage all together
  reader.parse_table_finegrain_column_lineages(file_path)
  ```

* **Bulk upload entities**
  * [Bulk Entities Excel Sample](./excel_bulk_entities_upload.py)
  * You want to dump entity information into excel and upload.
  * You want to provide some simple relationship mapping (e.g. the columns of a table).
  * Your entities may exist and you want them updated or they do not exist and you want them created.
* **Create Lineage Between Two Existing Entities**
  * [Update / Create Lineage Between Existing Entities](./excel_update_lineage_upload.py)
  * You have two existing entities (an input and output) but there is no lineage between them.
  * You want to create a "process entity" that represents the process that ties the two tables together.
* **Create Lineage Between Two Existing Entities with Column Mappings**
  * [Update / Create Lineage Between Existing Entities with Column Mappings](./excel_update_lineage_with_mappings_upload.py)
  * You have two existing entities (an input and output) but there is no lineage between them.
  * You want to create a "process entity" that represents the process that ties the two tables together.
  * In addition, you want to use the Azure Purview Column Mapping / Column Lineage UI feature.
  * You'll do this across the `UpdateLineage` and `ColumnMapping` tabs.
* **Create Entities and Lineage From Scratch**
  * [Custom Table and Column Lineage](./excel_custom_table_column_lineage.py)
  * You want to create your tables with schema and assign lineage between those tables.
  * You'll do this across the `BulkEntities` and `UpdateLineage` tabs.
* **Creating Custom DataSet Types**
  * [Custom Type Excel Sample](./excel_custom_type_and_entity_upload.py)
  * You have a custom dataset type you want to create with many attributes.
  * You want to upload an entity using that custom type as well.
* **(Deprecated) Hive Bridge Style Table and Column Lineage**
  * [Hive Style Table and Column Lineage Excel Sample](./hive_style_table_column_lineage.py)
  * Deprecation Warning: This example uses deprecated features which will be removed eventually.
  * You are willing to use a custom type to capture more data about lineage.
  * You are interested in capturing more complex column level lineage.
  * None of the entities you want to upload exist in your catalog.

Each sample linked above is stand alone and will create an excel spreadsheet with all of the data to be uploaded. It will then parse that spreadsheet and then upload to your data catalog.

I would strongly encourage you to run this in a dev / sandbox environment since it's a bit frustrating to find and delete the created entities.

## Requirements

* Follow the steps to install the latest version of PyApacheAtlas and its dependencies on the main ReadMe.
* You'll need a Service Principal (for Azure Data Catalog) with the Catalog Admin role.
* You'll need to set the following environment variables.

```bash
set TENANT_ID=YOUR_TENANT_ID
set CLIENT_ID=YOUR_SERVICE_PRINCIPAL_CLIENT_ID
set CLIENT_SECRET=YOUR_SERVICE_PRINCIPAL_CLIENT_SECRET
set PURVIEW_NAME=YOUR_PURVIEW_ACCOUNT_SERVICE_NAME
```

## Deleting Demo Entities and Types

* You have to delete entities based on GUID and types can be deleted by name.
* If you're following along with the built-in demos, search for 'pyapacheatlas' to find the majority of the entities.
* To find the guid, select the asset from your search and grab the guid from the URL.

```python
# Delete an Entity
client.delete_entity(guid=["myguid1","myguid2"])

# Delete a Type Definition
client.delete_type(name="mytypename")
```
