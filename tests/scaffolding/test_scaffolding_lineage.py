import json
from pyapacheatlas.scaffolding import column_lineage_scaffold


def test_column_lineage_scaffolding():
    scaffolding = column_lineage_scaffold("demo", use_column_mapping=True)

    results = scaffolding

    expected = json.loads("""{
  "entityDefs": [
    {
      "category": "ENTITY",
      "name": "demo_column",
      "attributeDefs": [],
      "relationshipAttributeDefs": [],
      "superTypes": [
        "DataSet"
      ]
    },
    {
      "category": "ENTITY",
      "name": "demo_table",
      "options": {
        "schemaElementsAttribute": "columns"
      },
      "attributeDefs": [],
      "relationshipAttributeDefs": [],
      "superTypes": [
        "DataSet"
      ]
    },
    {
      "category": "ENTITY",
      "name": "demo_column_lineage",
      "attributeDefs": [
        {
          "name": "dependencyType",
          "typeName": "string",
          "isOptional": false,
          "cardinality": "SINGLE",
          "valuesMinCount": 1,
          "valuesMaxCount": 1,
          "isUnique": false,
          "isIndexable": false,
          "includeInNotification": false
        },
        {
          "name": "expression",
          "typeName": "string",
          "isOptional": true,
          "cardinality": "SINGLE",
          "valuesMinCount": 0,
          "valuesMaxCount": 1,
          "isUnique": false,
          "isIndexable": false,
          "includeInNotification": false
        }
      ],
      "relationshipAttributeDefs": [],
      "superTypes": [
        "Process"
      ]
    },
    {
      "category": "ENTITY",
      "name": "demo_process",
      "attributeDefs": [
        {
          "name": "columnMapping",
          "typeName": "string",
          "cardinality": "SINGLE",
          "includeInNotification": false,
          "isIndexable": false,
          "isOptional": true,
          "isUnique": false,
          "valuesMaxCount":1,
          "valuesMinCount":0
        }
      ],
      "relationshipAttributeDefs": [],
      "superTypes": [
        "Process"
      ]
    }
  ],
  "relationshipDefs": [
    {
      "category": "RELATIONSHIP",
      "name": "demo_table_columns",
      "endDef1": {
        "type": "demo_table",
        "name": "columns",
        "isContainer": true,
        "cardinality": "SET",
        "isLegacyAttribute": false
      },
      "endDef2": {
        "type": "demo_column",
        "name": "table",
        "isContainer": false,
        "cardinality": "SINGLE",
        "isLegacyAttribute": false
      },
      "relationshipCategory": "COMPOSITION"
    },
    {
      "category": "RELATIONSHIP",
      "name": "demo_process_column_lineage",
      "endDef1": {
        "type": "demo_column_lineage",
        "name": "query",
        "isContainer": false,
        "cardinality": "SINGLE",
        "isLegacyAttribute": true
      },
      "endDef2": {
        "type": "demo_process",
        "name": "columnLineages",
        "isContainer": true,
        "cardinality": "SET",
        "isLegacyAttribute": false
      },
      "relationshipCategory": "COMPOSITION"
    }
  ]
}
""")
    assert(expected == results)