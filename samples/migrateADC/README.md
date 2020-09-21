# "Migrating" Between Data Catalogs

While Atlas and the Azure Data Catalog do not have "true" migration patterns, we can carefully mimic this process by extracting existing terms, assets, and relationships and then properly uploading them to any new data catalog.

The process looks like the following:

* Extract glossary terms and entities
* Remove the relationship attributes / relations and save them off.
* Upload the terms and entities without relationship attributes.
* Record the original and new guids for terms and entities.
* Remap the guids (from old to new)
* Upload the relationships.

## Assumptions:

* You are NOT using Term Templates.
* You have already uploaded any custom type definitions to your Data Catalog.

## Instructions

* Update the `/samples/migrateADC/config.ini` with your service principal information for new and old "clients".
* Run the following scripts in order, from the root of the pyapacheatlas project directory.
* `setup_folders.py`: Create the necessary folder structure.
* `glossary_terms.py`: Extract and upload the glossary terms.
  * Limitation: Does not support Term Templates (i.e. custom attributes on the glossary).
* `entities.py`: Extract and upload the entities.
* `relationships.py`: For discovered glossary and entity relationships, recreate the relationship.

## Possible Improvements

* Maintain a "deadletter" state to identify which entities / terms failed to upload.
   * This is already complete for relationships
