# Partial Purview Migration

This sample provides a means of 'partially' migrating an Azure Purview
services changes to another Azure Purview service that has scanned
the same data sources. It supports overwriting Contacts (experts, owners),
descriptions, appending classifications, and appending glossary terms to
assets that exist in both services.

This sample is useful for those who have invested time in annotating
an existing Purview service but want to move those updates to a
different catalog. This sample should not be used on a regular basis
to move annotations, instead Stewards should have annotate the true
Purview service rather than maintaining multiple Purview services.

## Getting Started

* You should have two Azure Purview Services
  * One with modifications ('old client') to contacts, descriptions, assets tagged with classifications or glossary terms
  * One without the above modifications ('new client') that will be receiving those updates.
  * **Both old client and new client should have the same classifications, glossary terms, and scanned assets**
    * **This sample only works on assets with the same qualified name and types**, you cannot use this sample (as is) to partially migrate non-prod asset changes to a prod Purview due to the scanned assets having different qualified name.
    * For example scanning `mssql://non-prod-server.database.windows.net` won't map automatically to another Purview instance that has scanned `mssql://prod-server.database.windows.net`.
* Install the latest version of PyApacheAtlas `pip install pyapacheatlas`
* Set up a Service Principal (or two) with access to one or both instances of Azure Purview.
* Set up your environment variables
  ```
  set PURVIEW_NAME=old-purview-service-name
  set NEW_PURVIEW_NAME=new-purview-service-name
  set AZURE_TENANT_ID=XXXX
  set AZURE_CLIENT_ID=XXXX
  set AZURE_CLIENT_SECRET=XXXX
  ```
  or, for Linux users
  ```
  export PURVIEW_NAME=old-purview-service-name
  export NEW_PURVIEW_NAME=new-purview-service-name
  export AZURE_TENANT_ID=XXXX
  export AZURE_CLIENT_ID=XXXX
  export AZURE_CLIENT_SECRET=XXXX
  ```
* Execute the script searching across all assets `python ./samples/migratePurviewPartially -s *`

## Advanced Used Cases


### Avoiding the 100,000 search results cap
There is a limitation with Azure Purview that your search results cannot provide more than 100,000 results.
Therefore, you may have to get tricky with the searching. You might want to limit your search by searching
for a specific name such as `myserver` to avoid hitting that 100,000 cap.

`python ./samples/migratePurviewPartially -s myserver`

### Specifying the Folder for Search Results and batch outputs
If you're specifying a specific search term, you may want to store the results of that search in a
specific folder so that the script only begins querying for data based on those search results.
The default behavior is to store search results in `./searches`. You can specify `--search-folder ./some/location` to change that default behavior.
You may also change where the pseudo "checkpoints" that are stored by specifying `--batch-folder ./some/other/location`.

### Thinking about Multiple Processes and Checkpoints
If you have a very large catalog, there's risk that this script will fail at some point just due to network
connectivity or some unhandled case (I'm not perfect).

If the job fails in the middle of processing updates, you can re-run the job, specifying the search-folder
and the batch-folder. The search-folder will contain all the entity guids found while crawling through
the search results. The batch-folder will contain all of the guids that have been seen and have successfully
processed. The script, in memory, will remove the guids found in the batch-folder from the search-folder guids.
This enables you to begin processing only on search results that have not been seen yet.

If you are considering splitting this into multiple processes, to speed up searching and processing, consider
multiple processes and specifying separate search-folders and batch-folders. You may have some duplicate
updates if your search results (or referred entities) overlap.
