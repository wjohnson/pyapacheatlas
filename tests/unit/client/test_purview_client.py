import json
import os
import sys
import warnings
sys.path.append('.')

import pytest

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core.client import AtlasClient, PurviewClient
from pyapacheatlas.core.util import PurviewLimitation, PurviewOnly

def test_purview_client():

    client = PurviewClient("DEMO")

    assert(client.endpoint_url == "https://demo.catalog.purview.azure.com/api/atlas/v2")
    assert(client.is_purview)

def test_purview_only_decorator():

    @PurviewOnly
    def temp(self):
        return 1
    AtlasClient.temp_func = temp
    client = AtlasClient("DEMO")
    
    with pytest.warns(RuntimeWarning):
        out = client.temp_func()
    assert(out ==1)

def test_purview_limited_decorator():

    @PurviewLimitation
    def temp(self):
        return 1
    PurviewClient.temp_func = temp
    client = PurviewClient("DEMO")
    
    with pytest.warns(RuntimeWarning):
        client.temp_func()
        out = client.temp_func()
    assert(out ==1)
