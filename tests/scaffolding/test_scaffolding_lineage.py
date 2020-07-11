import json
from pyapacheatlas.scaffolding import column_lineage_scaffold


def test_column_lineage_scaffolding():
    scaffolding = column_lineage_scaffold("demo", useColumnMapping=True)

    results = json.dumps(scaffolding).replace(" ", "")

    expected = """{
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
      "attributeDefs": [],
      "relationshipAttributeDefs": [],
      "superTypes": [
        "DataSet"
      ]
    },
    {
      "category": "ENTITY",
      "name": "demo_column_lineage",
      "attributeDefs": [],
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
          "isIndexable": false,
          "isOptional": true,
          "isUnique": false
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
        "isLegacyAttribute": true
      },
      "endDef2": {
        "type": "demo_column",
        "name": "table",
        "isContainer": false,
        "cardinality": "SINGLE",
        "isLegacyAttribute": true
      }
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
      }
    }
  ]
}
""".strip().replace('\n', ' ').replace(" ", "")
    assert(expected == results)