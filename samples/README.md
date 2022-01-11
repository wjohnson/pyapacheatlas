# PyApacheAtlas Samples

The below samples demonstrate the Excel functionality, the core classes and methods,
and the miscellaneous scenarios that have come up a few times with Purview customers.

## Using the Excel Readers

The [Excel Samples](./excel/README.md) provides example data and generates
the Excel templates for you. The samples demonstrate:

* **Bulk upload entities**
  * [Bulk Entities Excel Sample](./excel/excel_bulk_entities_upload.py)
* **Hive Bridge Style Table and Column Lineage**
  * [Custom Table and Column Lineage Excel Sample](./excel/excel_custom_table_column_lineage.py)
* **Creating Custom DataSet Types**
  * [Custom Type Excel Sample](./excel/excel_custom_type_and_entity_upload.py)
* **Create Lineage Between Two Existing Entities**
  * [Update / Create Lineage Between Existing Entities](./excel/excel_update_lineage_upload.py)

## Using the PyApacheAtlas Core Classes / REST API Abstraction

The [Create, Read, Update, and Delete](./CRUD/README.md) samples demonstrate how to do basic operations
with the core methods and classes of PyApachAtlas. The sample demonstrate:

* **Create**
  * Create [classifications on entities](./CRUD/create_entity_and_classification.py).
  * Create [entities and lineage between multiple entities](./CRUD/create_entity_and_lineage.py).
  * Create [relationships](./CRUD/create_relationships.py) in a few different ways.
* **Read**
  * Read the [classifications on an entity](./CRUD/read_classification.py).
  * Get an entity by [by Guid or by qualified name and type](./CRUD/read_entity_guid_or_name.py).
  * [Search for an entity by name](./CRUD/read_search_by_name.py).
* **Update**
  * Update an [existing entity and lineage](./CRUD/update_entity_and_lineage.py).
  * Update an [entity with a term by discovering related terms](./CRUD/update_entities_with_term.py) through search.
* **Delete**
  * Delete an entity [by Guid or by qualified name and type](./CRUD/delete_entity.py).
  * Delete a [classification from an entity](./CRUD/delete_classification.py).

## Additional Samples

In addition, some special scenarios are covered below:

* Creating an Entity based on an [Azure Databricks DataFrame](./databricks_catalog_dataframe.py).
* Creating a ["Process Workflow" entity](./process_with_workflow_steps.py) that demonstrates how you might record the steps in a process.
