import argparse
import json
import os

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import AtlasClient  # Communicate with your Atlas server
from pyapacheatlas.readers import ExcelConfiguration, ExcelReader

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", "--p", help="Path to Excel Template")
    args = parser.parse_args()

    # Authenticate against your Atlas server
    oauth = ServicePrincipalAuthentication(
        tenant_id=os.environ.get("TENANT_ID", ""),
        client_id=os.environ.get("CLIENT_ID", ""),
        client_secret=os.environ.get("CLIENT_SECRET", "")
    )
    client = AtlasClient(
        endpoint_url=os.environ.get("ENDPOINT_URL", ""),
        authentication=oauth
    )

    ec = ExcelConfiguration()
    reader = ExcelReader(ec)

    results = reader.parse_bulk_entities(args.path)

    print(json.dumps(results, indent=2))

    input(">>>>Ready to upload?")

    upload_results = client.upload_entities(results)

    print(json.dumps(upload_results, indent=2))
