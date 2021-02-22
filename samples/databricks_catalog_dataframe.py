# Databricks notebook source
import os
from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient, AtlasEntity, AtlasProcess, TypeCategory
from pyapacheatlas.core.util import GuidTracker
from pyapacheatlas.core.typedef import AtlasAttributeDef, EntityTypeDef, RelationshipTypeDef

# Add your credentials here or set them as environment variables
tenant_id = ""
client_id = ""
client_secret = ""
purview_account_name = ""

# COMMAND ----------

oauth = ServicePrincipalAuthentication(
        tenant_id=os.environ.get("TENANT_ID", tenant_id),
        client_id=os.environ.get("CLIENT_ID", client_id),
        client_secret=os.environ.get("CLIENT_SECRET", client_secret)
    )
client = PurviewClient(
    account_name = os.environ.get("PURVIEW_NAME", purview_account_name),
    authentication=oauth
)
guid = GuidTracker()

# COMMAND ----------

# Set up a few types and relationships
# This is a one time thing but necessary to make the demo work
# It also demonstrates how you can capture different attributes
# for your dataframes, dataframe columns, and jobs.
type_spark_df = EntityTypeDef(
  name="custom_spark_dataframe",
  attributeDefs=[
    AtlasAttributeDef(name="format")
  ],
  superTypes = ["DataSet"],
  options = {"schemaElementAttribute":"columns"}
 )
type_spark_columns = EntityTypeDef(
  name="custom_spark_dataframe_column",
  attributeDefs=[
    AtlasAttributeDef(name="data_type")
  ],
  superTypes = ["DataSet"],
)
type_spark_job = EntityTypeDef(
  name="custom_spark_job_process",
  attributeDefs=[
    AtlasAttributeDef(name="job_type",isOptional=False),
    AtlasAttributeDef(name="schedule",defaultValue="adHoc")
  ],
  superTypes = ["Process"]
)

spark_column_to_df_relationship = RelationshipTypeDef(
  name="custom_spark_dataframe_to_columns",
  relationshipCategory="COMPOSITION",
  endDef1={
          "type": "custom_spark_dataframe",
          "name": "columns",
          "isContainer": True,
          "cardinality": "SET",
          "isLegacyAttribute": False
      },
  endDef2={
          "type": "custom_spark_dataframe_column",
          "name": "dataframe",
          "isContainer": False,
          "cardinality": "SINGLE",
          "isLegacyAttribute": False
      }
)

typedef_results = client.upload_typedefs(
  entityDefs = [type_spark_df, type_spark_columns, type_spark_job ],
  relationshipDefs = [spark_column_to_df_relationship],
  force_update=True)
print(typedef_results)


# COMMAND ----------

# No we actually do some databricks work
df = spark.read.csv("/databricks-datasets/flights/departuredelays.csv",header=True, inferSchema=True)

# COMMAND ----------

# Do some transformations

# COMMAND ----------

display(df)

# COMMAND ----------

# Now we begin to do some Atlas uploads using the types created above.
# Get the notebook path as it will be part of our process' name.
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()

# COMMAND ----------

# Create an asset for the input data frame.
atlas_input_df = AtlasEntity(
  name="demo_dbfs_delays_data",
  qualified_name = "pyapacheatlas://demo_dbfs_delays_data",
  typeName="custom_spark_dataframe",
  guid=guid.get_guid(),
)

# Create a process that represents our notebook and has our input
# dataframe as one of the inputs.
process = AtlasProcess(
  name="demo_cluster"+notebook_path,
  qualified_name = "pyapacheatlas://demo_cluster"+notebook_path,
  typeName="custom_spark_job_process",
  guid=guid.get_guid(),
  attributes = {"job_type":"notebook"},
  inputs = [atlas_input_df],
  outputs = [] # No outputs for this demo, but otherwise, repeat what you did you the input dataframe.
)

# Iterate over the input data frame's columns and create them.
# Note: This is an add, not a delete. If the dataframe already exists in
# Atlas/Data Catalog, this sample is not smart enough to prune any 'orphan'
# columns. They will continue to exist and point to the dataframe.
atlas_input_df_columns = []
for column in df.schema:
  temp_column = AtlasEntity(
    name = column.name,
    typeName = "custom_spark_dataframe_column",
    qualified_name = "pyapacheatlas://demo_dbfs_delays_data#"+column.name,
    guid=guid.get_guid(),
    attributes = {"data_type":str(column.dataType)},
    relationshipAttributes = {"dataframe":atlas_input_df.to_json(minimum=True)}
  )
  atlas_input_df_columns.append(temp_column)

# COMMAND ----------

# Prepare all the entities as a batch to be uploaded.
batch = [process, atlas_input_df] + atlas_input_df_columns

# COMMAND ----------

# Upload all entities!
client.upload_entities(batch=batch)
