import json
import os
import configparser
import argparse
import csv
import pyodbc 
import pandas as pd

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core.typedef import EntityTypeDef, TypeCategory
from pyapacheatlas.core import (
    AtlasAttributeDef,
    AtlasEntity,
    PurviewClient,
    RelationshipTypeDef
)
from pyapacheatlas.core.util import GuidTracker
DB_ENTITY_NAME ="custom_aws_redshift_db"
SCHEMA_ENTITY_NAME ="custom_aws_redshift_schema"
TABLE_ENTITY_NAME ="custom_aws_redshift_table"
COLUMN_ENTITY_NAME ="custom_aws_redshift_column"
DB_SCHEMA_RELATIONSHIP_NAME="custom_aws_redshift_db_schema"
SCHEMA_TABLE_RELATIONSHIP_NAME="custom_aws_redshift_schema_table"
TABLE_COLUMN_RELATIONSHIP_NAME="custom_aws_redshift_table_column"
DB_COLUMN_NAME="table_catalog"
SCHEMA_COLUMN_NAME="table_schema"
TABLE_COLUMN_NAME="table_name"
COLUMN_COLUMN_NAME="column_name"
DATATYPE_COLUMN_NAME="data_type"

def createEntityDefinitions(client):
    # -- Add DB
    entityDefs = []
    entityDefs.append(EntityTypeDef(
        name=DB_ENTITY_NAME,
        superTypes=["azure_resource"],
        description=DB_ENTITY_NAME,
        typeVersion="1.0",
        serviceType="Amazon Redshift Database"
    ))
    #-- Add Schema
    entityDefs.append(EntityTypeDef(
        name=SCHEMA_ENTITY_NAME,
        superTypes=["Asset"],
        description=SCHEMA_ENTITY_NAME,
        typeVersion="1.0",
        serviceType="Amazon Redshift Database"
    ))
    #-- Add Table
    entityDefs.append(EntityTypeDef(
        name=TABLE_ENTITY_NAME,
        superTypes=["DataSet"],
        description=TABLE_ENTITY_NAME,
        typeVersion="1.0",
        serviceType="Amazon Redshift Database"
    ))
    #-- Add Column
    columnDef = EntityTypeDef(
        name=COLUMN_ENTITY_NAME,
        superTypes=["DataSet"],
        description=COLUMN_ENTITY_NAME,
        serviceType="Amazon Redshift Database"
    )
    columnDef.addAttributeDef(
        AtlasAttributeDef(name="comment", typeName="string", isOptional=True))
    entityDefs.append(columnDef)

    relationshipDefs = []
    #-- Add Relationships
    relationshipDefs.append(RelationshipTypeDef(
        name=DB_SCHEMA_RELATIONSHIP_NAME,
        attributeDefs=[],
        relationshipCategory="COMPOSITION", # Means the child can't exist  without the parent
        endDef1={ # endDef1 decribes what the parent will have as an attribute
            "type":DB_ENTITY_NAME, # Type of the parent
            "name":"schemas", # What the parent will have
            "isContainer": True,
            "cardinality":"SET", # This is related to the cardinality, in this case the parent Server will have a SET of Models.
            "isLegacyAttribute":False
        },
        endDef2={ # endDef2 decribes what the child will have as an attribute
            "type":SCHEMA_ENTITY_NAME, # Type of the child
            "name":"db", # What the child will have
            "isContainer":False,
            "cardinality":"SINGLE",
            "isLegacyAttribute":False
        }
    ))
    relationshipDefs.append(RelationshipTypeDef(
        name=SCHEMA_TABLE_RELATIONSHIP_NAME,
        attributeDefs=[],
        relationshipCategory="COMPOSITION", 
        endDef1={ 
            "type":SCHEMA_ENTITY_NAME, 
            "name":"tables", 
            "isContainer": True,
            "cardinality":"SET", 
            "isLegacyAttribute":False
        },
        endDef2={ 
            "type":TABLE_ENTITY_NAME,
            "name":"schema", 
            "isContainer":False,
            "cardinality":"SINGLE",
            "isLegacyAttribute":False
        }
    ))
    relationshipDefs.append(RelationshipTypeDef(
        name=TABLE_COLUMN_RELATIONSHIP_NAME,
        attributeDefs=[],
        relationshipCategory="COMPOSITION", 
        endDef1={ 
            "type":TABLE_ENTITY_NAME, 
            "name":"columns", 
            "isContainer": True,
            "cardinality":"SET", 
            "isLegacyAttribute":False
        },
        endDef2={ 
            "type":COLUMN_ENTITY_NAME, 
            "name":"table", 
            "isContainer":False,
            "cardinality":"SINGLE",
            "isLegacyAttribute":False
        }
    ))
    return client.upload_typedefs(entityDefs = entityDefs,relationshipDefs=relationshipDefs,force_update=True)

def uploadEntity(client,entity):
    client.upload_entities(batch=[entity])
    #print(entity)

def uploadRelationship(client,relationShipEntity):
    client.upload_relationship(relationShipEntity)
    #print(relationship)

def createEntities(client,redshiftMetaData):
    gt = GuidTracker()
    for db in redshiftMetaData:
        dbGuid = gt.get_guid()
        dbe = AtlasEntity(
            name=db["name"], typeName=DB_ENTITY_NAME, qualified_name=db["qualifiedName"],guid=dbGuid
        )
        uploadEntity(client,dbe)
        #-------------------------------------
        #  Create schema entities
        for schema in db["schemas"]:
            schemaGuid = gt.get_guid()
            sce = AtlasEntity(
                name=schema["name"],typeName=SCHEMA_ENTITY_NAME,qualified_name=schema["qualifiedName"],guid=schemaGuid
            )
            uploadEntity(client,sce)
            relationship = {
                "typeName": DB_SCHEMA_RELATIONSHIP_NAME,
                "attributes": {},
                "guid": -100,
                "provenanceType": 0,
                "end1": {
                    "guid": dbGuid,
                    "typeName": DB_ENTITY_NAME,
                    "uniqueAttributes": {"qualifiedName": db["qualifiedName"]}
                },
                "end2": {
                    "guid": schemaGuid,
                    "typeName": SCHEMA_ENTITY_NAME,
                    "uniqueAttributes": {"qualifiedName": schema["qualifiedName"]}
                }
            }
            uploadRelationship(client, relationship)
            #------------------------------------------------------
            #  Create table entities
            for table in schema["tables"]:
                tableGuid = gt.get_guid()
                te = AtlasEntity(
                    name=table["name"],typeName=TABLE_ENTITY_NAME,qualified_name=table["qualifiedName"],guid=tableGuid
                )
                uploadEntity(client,te)
                relationship = {
                    "typeName": SCHEMA_TABLE_RELATIONSHIP_NAME,
                    "attributes": {},
                    "guid": -100,
                    "provenanceType": 0,
                    "end1": {
                        "guid": schemaGuid,
                        "typeName": SCHEMA_ENTITY_NAME,
                        "uniqueAttributes": {"qualifiedName": schema["qualifiedName"]}
                    },
                    "end2": {
                        "guid": tableGuid,
                        "typeName": TABLE_ENTITY_NAME,
                        "uniqueAttributes": {"qualifiedName": table["qualifiedName"]}
                    }
                }
                uploadRelationship(client,relationship)

                #  Create column entities
                for column in table["columns"]:
                    columnGuid = gt.get_guid()
                    ce = AtlasEntity(name=column["name"],typeName=COLUMN_ENTITY_NAME,
                        qualified_name=column["qualifiedName"],guid=columnGuid,
                        attributes={
                            "type": column["type"]
                        }
                    )
                    uploadEntity(client,ce)
                    relationship = {
                        "typeName": TABLE_COLUMN_RELATIONSHIP_NAME,
                        "attributes": {},
                        "guid": -100,
                        "provenanceType": 0,
                        "end1": {
                            "guid": tableGuid,
                            "typeName": TABLE_ENTITY_NAME,
                            "uniqueAttributes": {"qualifiedName": table["qualifiedName"]}
                        },
                        "end2": {
                            "guid": columnGuid,
                            "typeName": COLUMN_ENTITY_NAME,
                            "uniqueAttributes": {"qualifiedName": column["qualifiedName"]}
                        }
                    }
                    uploadRelationship(client, relationship) 
                    print(column["name"])   

def cleanup(client):
    search = client.discovery.search_entities("\"Amazon Redshift Database\"")
    for entity in search:
        client.delete_entity(guid=[entity["id"]])
        #print(json.dumps(entity, indent=2))

    client.delete_type(name=TABLE_COLUMN_RELATIONSHIP_NAME)
    client.delete_type(name=SCHEMA_TABLE_RELATIONSHIP_NAME)
    client.delete_type(name=DB_SCHEMA_RELATIONSHIP_NAME)
    client.delete_type(name=DB_ENTITY_NAME)
    client.delete_type(name=SCHEMA_ENTITY_NAME)
    client.delete_type(name=TABLE_ENTITY_NAME)
    client.delete_type(name=COLUMN_ENTITY_NAME)

def getRedshiftMetadata(redshiftConnectionString,redshiftJdbcConnection):
    query = "SELECT * FROM information_schema.columns WHERE table_schema != 'pg_catalog' AND table_schema != 'information_schema' AND table_schema != 'pg_internal'"
    conn = pyodbc.connect(redshiftConnectionString)
    df = pd.read_sql_query(query, conn)
    jsonSchema = []
    df = df.sort_values(by=[DB_COLUMN_NAME,SCHEMA_COLUMN_NAME,TABLE_COLUMN_NAME,COLUMN_COLUMN_NAME], ascending=True)
    dbs = df.groupby([DB_COLUMN_NAME]).groups
    for db in dbs:
        currentdb = { "name": db,"qualifiedName" : redshiftJdbcConnection,"schemas" :[]}
        schemas = df[df[DB_COLUMN_NAME] == db].groupby([SCHEMA_COLUMN_NAME]).groups
        for schema in schemas:
            currentSchema = {"name": schema,
                "qualifiedName" : redshiftJdbcConnection + "/" + schema,
                "tables" :[]
            }
            tables = df[(df[DB_COLUMN_NAME] == db) & (df[SCHEMA_COLUMN_NAME] == schema)].groupby([TABLE_COLUMN_NAME]).groups
            for table in tables:
                currentTable= {"name": table,
                    "qualifiedName" : redshiftJdbcConnection + "/" + schema + "/" + table,
                    "columns" :[]
                }
                columns = df[(df[DB_COLUMN_NAME] == db) & (df[SCHEMA_COLUMN_NAME] == schema) & 
                             (df[TABLE_COLUMN_NAME] == table)].groupby([COLUMN_COLUMN_NAME, DATATYPE_COLUMN_NAME]).groups
                for column, datatype in columns:
                    currentColumn= {"name": column,
                        "qualifiedName" : redshiftJdbcConnection + "/" + schema + "/" + table + "/" + column,
                        "type" : datatype
                    }
                    currentTable["columns"].append(currentColumn)

                currentSchema["tables"].append(currentTable)

            currentdb["schemas"].append(currentSchema)
        
        jsonSchema.append(currentdb)

    return jsonSchema

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.ini")
    args, _ = parser.parse_known_args()

    config = configparser.ConfigParser()
    config.read(args.config)
    
    oauth = ServicePrincipalAuthentication(
        tenant_id=config["PurviewClient"]["TENANT_ID"],
        client_id=config["PurviewClient"]["CLIENT_ID"],
        client_secret=config["PurviewClient"]["CLIENT_SECRET"]
    )
    client = PurviewClient(
        account_name=config["PurviewClient"]["PURVIEW_ACCOUNT_NAME"],
        authentication=oauth
    )
    
    redshiftConnectionString = config["Redshift"]["REDSHIFT_CONNECTION_STRING"].strip("'")
    redshiftJdbcConnection = config["Redshift"]["REDSHIFT_JDBC_CONNNECTION"].strip("'")

    redshiftMetadata = getRedshiftMetadata(redshiftConnectionString,redshiftJdbcConnection)
    with open('redshift_metadata.json', 'w') as f:
       json.dump(redshiftMetadata, f)

    createEntityDefinitions(client)

    createEntities(client, redshiftMetadata)

    print(redshiftMetadata)

    # cleanup(client)
    
    