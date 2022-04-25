# Create, Read, Update, Delete Operations

This section of samples provides examples on how to use the core
PurviewClient and AtlasEntity objects to create, read, update, and delete
entities using PyApacheAtlas.

If you are interested in using the built-in Excel functionality, see the [excel samples](../excel/README.md).

* **Create**
  * Create [classifications on entities](./create_entity_and_classification.py).
  * Create [entities and lineage between multiple entities](./create_entity_and_lineage.py).
  * Create [relationships](./create_relationships.py) in a few different ways.
* **Read**
  * Read the [classifications on an entity](./read_classification.py).
  * Get an entity by [by Guid or by qualified name and type](./read_entity_guid_or_name.py).
  * [Search for an entity by name](./read_search_by_name.py).
* **Update**
  * Update an [existing entity and lineage](./update_entity_and_lineage.py).
  * Update an [entity with a term by discovering related terms](./update_entities_with_term.py) through search.
* **Delete**
  * Delete an entity [by Guid or by qualified name and type](./delete_entity.py).
  * Delete a [classification from an entity](./delete_classification_from_entity.py).
* **Advanced Features**
  * Create, Read, Update, Delete [Business Metadata](./crud_business_metadata.py).
  * Create, Read, Update, Delete [Custom Attributes](./crud_custom_attributes.py).
  * Create, Read, Update, Delete [Custom Labels](./crud_custom_labels.py).
