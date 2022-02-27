import json
import os
import sys
import warnings
sys.path.append('.')

import pytest

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core.client import AtlasClient, PurviewClient
from pyapacheatlas.core.util import PurviewLimitation, PurviewOnly

def test_purview_client_integration():
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

    results = client.glossary.get_glossary()

    assert(results is not None)
