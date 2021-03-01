# Migrating Azure Data Catalog Gen 1 to Azure Purview

The current set of samples provides migration support for Glossary Terms in
Azure Data Catalog Gen 1 to Azure Purview.

## Glossary Term Migration

The `migrate_terms.py` script performs the following tasks to migrate your ADC Gen 1
terms to Azure Purview.

* Download all glossary terms in your ADC Gen 1.
* Convert glossary terms to a csv.
* Import the csv of glossary terms to Azure Purview.

In order to accomplish this, you'll need to create a config.ini file that looks
like the below text block.  Your Tenant Id, Client Ids, and Client secret need
to represent at least one service principal that has access to your ADC Gen 1
and your Azure Purview service. The service principals should be a user in ADC
Gen 1 and have Purview Data Curator for Purview.

```
[Default]
RootFolder = .
ADCTermsPath = %(RootFolder)s/adc_terms.json
PurviewImportPath = %(RootFolder)s/purview_terms.csv

[ADCGen1Client]
TENANT_ID=xxx-xxx-xxx-xxx-xxx
CLIENT_ID=xxx-xxx-xxx-xxx-xxx
CLIENT_SECRET=xxx
CATALOG_NAME=xxx
GLOSSARY_NAME=DefaultGlossary

[PurviewClient]
TENANT_ID=xxx-xxx-xxx-xxx-xxx
CLIENT_ID=xxx-xxx-xxx-xxx-xxx
CLIENT_SECRET=xxx
PURVIEW_ACCOUNT_NAME=xxx
```

Execute the script by calling `python ./samples/migrateADCGen1/migrate_terms.py`.\

# Asset Migration (Work in Process)

After you have scanned your assets with Azure Purview, you can use this utility
to extract the following annotations from your ADC Gen 1.

* termTags
* columnTermTags
* descriptions
* columnDescriptions
* friendlyName: Replaces the "name" attribute.
* experts: Known issue, this will overwrite any existing owners and experts

Execute the script by navigating to the `./samples/migrateADCGen1` folder and
calling `python migrate_assets.py --terms <path to terms file>`.\

## Extending the AssetMapper and AssetFactory class

When you add a new asset mapper type, add it in the `mappers` folder and update
the `__init__.py` to include the objects in the main mappers package. In addition
you should update the AssetFactory to include your new type.

* `__init__` Provide typeName and columnTypeName (if asset type may ever have columnTermTags or columnDescriptions)
* `qualified_name` Define how the Purview qualified name may be extract from the asset's content. Likely coming from the asset's `properties.dsl.address` object.
* `column_qualified_name_pattern` Define how the Purview qualified name may be extracted for the column type relating to this asset.
* `entity` Returns the AtlasEntity object. You should extend this to fill in any required attributes or relationship attributes.

These methods likely do not have to be updated.
* `partial_entity_updates` Base class only provides support for partial update with friendly name to name and description field. Can be extending by taking the super() function and extending the returned dictionary. Specifically the dict within the attributes field.
* `partial_column_updates` Base class only provides support for columnDescriptions. Can be extended by taking the super() function and extending the list of returned dictionaries.
* `glossary_entity_relationships` Likely you don't have to extend this. Returns the relationship objects between the given term and the asset.
* `glossary_column_relationships` Likely you don't have to extend this. Returns the relationship objects between the given term and the columns for this asset.