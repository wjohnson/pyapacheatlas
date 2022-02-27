import os
import sys
sys.path.append('.')

import pytest

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import AtlasEntity
from pyapacheatlas.core.client import PurviewClient
from pyapacheatlas.core.util import AtlasException

oauth = ServicePrincipalAuthentication(
        tenant_id=os.environ.get("TENANT_ID", ""),
        client_id=os.environ.get("CLIENT_ID", ""),
        client_secret=os.environ.get("CLIENT_SECRET", "")
    )
client = PurviewClient(
    account_name = os.environ.get("PURVIEW_NAME", ""),
    authentication=oauth
)


def test_purview_search_iterates_safely():
    ae = AtlasEntity(
        name="there_can_be_only_one",
        qualified_name="pyapacheatlas://there_can_be_only_one",
        guid=-100,
        typeName="hive_table"
    )

    upload_success = client.upload_entities(ae)    

    search_results = client.discovery.search_entities(r"there_can_be_only_one")

    counter = 0
    for entity in search_results:
        len(entity["id"])
        counter = counter + 1
    
    assert(counter == 1)


def test_purview_search_iterates_safely_over_multiple():
    ae = AtlasEntity(
        name="there_can_be_only_two",
        qualified_name="pyapacheatlas://there_can_be_only_two_00",
        guid=-100,
        typeName="hive_table"
    )

    ae2 = AtlasEntity(
        name="there_can_be_only_two",
        qualified_name="pyapacheatlas://there_can_be_only_two_01",
        guid=-101,
        typeName="hive_table"
    )

    upload_success = client.upload_entities([ae, ae2])    

    search_results = client.discovery.search_entities(r"there_can_be_only_two")

    counter = 0
    for entity in search_results:
        len(entity["id"])
        counter = counter + 1
    
    assert(counter == 2)

def test_purview_search_iterates_safely_over_none():

    try:
        e = client.get_entity(qualifiedName="this_should_never_exist")
        if e:
            _ = client.delete_entity(e["guid"])
    except AtlasException:
        # Presumably this should not make it past get_entity
        # So catch the Atlas error and move on
        pass
    
    search_results = client.discovery.search_entities(r"this_should_never_exist")

    counter = 0
    for entity in search_results:
        len(entity["id"])
        counter = counter + 1
    
    assert(counter == 0)


    