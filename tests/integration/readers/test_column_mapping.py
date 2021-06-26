import os
import sys
sys.path.append('.')

import pytest

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import AtlasEntity, AtlasProcess, EntityTypeDef, AtlasAttributeDef
from pyapacheatlas.core.client import PurviewClient
from pyapacheatlas.readers.reader import Reader, ReaderConfiguration

def test_reader_column_mapping():
    # Authenticate against your Purview service
    oauth = ServicePrincipalAuthentication(
        tenant_id=os.environ.get("TENANT_ID", ""),
        client_id=os.environ.get("CLIENT_ID", ""),
        client_secret=os.environ.get("CLIENT_SECRET", "")
    )
    client = PurviewClient(
        account_name = os.environ.get("PURVIEW_NAME", ""),
        authentication=oauth
    )

    custom_proc_type = EntityTypeDef(
        "integrationCustomProcessWithMapping",
        superTypes=["Process"]
    )
    custom_proc_type.addAttributeDef(
        AtlasAttributeDef("columnMapping",typeName="string", isOptional=True)
    )

    custom_types = client.upload_typedefs(entityDefs=[custom_proc_type], force_update=True)
    assert(custom_types)


    # Create some dummy entities
    src_ae = AtlasEntity(
        "integrationsourcecolmap",
        "DataSet",
        "pyapacheatlas://integrationsourcecolmap",
        guid="-1"
    )

    snk_ae = AtlasEntity(
        "integrationsinkcolmap",
        "DataSet",
        "pyapacheatlas://integrationsinkcolmap",
        guid="-2"
    )

    proc = AtlasProcess(
        "integrationprocesscolmap",
        "integrationCustomProcessWithMapping",
        "pyapacheatlas://integrationprocesscolmap",
        inputs=[src_ae],
        outputs=[snk_ae]
    )

    entities = client.upload_entities([src_ae, snk_ae, proc])
    

    rc = ReaderConfiguration()
    reader = Reader(rc)

    json_rows = [
            {"Source qualifiedName": "pyapacheatlas://integrationsourcecolmap", 
            "Source column":"A1", "Target qualifiedName": "pyapacheatlas://integrationsinkcolmap", 
            "Target column": "B1", "Process qualifiedName": "pyapacheatlas://integrationprocesscolmap", 
            "Process typeName": "integrationCustomProcessWithMapping", "Process name": "integrationprocesscolmap"},
            {"Source qualifiedName": "pyapacheatlas://integrationsourcecolmap", 
            "Source column":"A2", "Target qualifiedName": "pyapacheatlas://integrationsinkcolmap", 
            "Target column": "B2", "Process qualifiedName": "pyapacheatlas://integrationprocesscolmap", 
            "Process typeName": "integrationCustomProcessWithMapping", "Process name": "integrationprocesscolmap"}
        ]

    parsed = reader.parse_column_mapping(json_rows)

    updated = client.upload_entities(parsed)

    assert(list(updated["guidAssignments"].values())[0] in entities["guidAssignments"].values())
