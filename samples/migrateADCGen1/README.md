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

Execute the script by calling `python ./samples/migrateADCGen1/migrate_terms.py`.
