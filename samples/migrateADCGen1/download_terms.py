import argparse
import configparser
import json
import requests

from pyapacheatlas.auth import ServicePrincipalAuthentication

config = configparser.ConfigParser()
config.read("./samples/migrateADCGen1/config.ini")


def download_gen1_terms(output_path):
    catalog_name = config["OldClient"]["CATALOG_NAME"]
    glossary_name = config["OldClient"]["GLOSSARY_NAME"]
    api_version = "2016-03-30"

    auth = ServicePrincipalAuthentication(
        tenant_id=config["OldClient"]["TENANT_ID"],
        client_id=config["OldClient"]["CLIENT_ID"],
        client_secret=config["OldClient"]["CLIENT_SECRET"]
    )

    auth.data.update({"resource":"https://api.azuredatacatalog.com"})

    enumerate_uri = f"https://api.azuredatacatalog.com/catalogs/{catalog_name}/glossaries/{glossary_name}/terms?api-version={api_version}"

    output = []
    while(True):
        results = requests.get(
            enumerate_uri,
            headers = auth.get_authentication_headers()
        )
        content = results.json()
        output.extend(content["value"])
        if "nextLink" not in content:
            break
        else:
            enumerate_uri = content["nextLink"]
    
    with open(output_path, 'w') as fp:
        json.dump(output, fp, indent=1)

    return output

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filepath", default="./gen1_terms.json")
    args = parser.parse_args()
    download_gen1_terms(args.filepath)