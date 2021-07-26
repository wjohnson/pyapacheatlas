import argparse
import configparser
import csv
import json
import os
import time

import requests

from mappers import AssetFactory

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core.client import PurviewClient
from pyapacheatlas.core.util import GuidTracker
from pyapacheatlas.core import AtlasException

class SearchURI():

    def __init__(self, catalog_name, api_version, search_terms="*", start_page=1, count=100):
        super().__init__()
        self.catalog_name = catalog_name
        self.api_version = api_version
        self.search_terms = search_terms
        self.start_page = start_page
        self.count = count

    @property
    def uri(self):
        output_uri = (
            f"https://api.azuredatacatalog.com/catalogs/{self.catalog_name}" +
            f"/search/search?api-version={self.api_version}&" +
            f"searchTerms={self.search_terms}&startPage={self.start_page}&" +
            f"count={self.count}&view=DataSource"
        )
        return output_uri

    def add_page(self):
        self.start_page = self.start_page + 1


def download_gen1_assets(config, search_terms="*", count=100, max_iter=1000):
    catalog_name = config["ADCGen1Client"]["CATALOG_NAME"]
    glossary_name = config["ADCGen1Client"]["GLOSSARY_NAME"]
    api_version = "2016-03-30"
    start_page = 1

    auth = ServicePrincipalAuthentication(
        tenant_id=config["ADCGen1Client"]["TENANT_ID"],
        client_id=config["ADCGen1Client"]["CLIENT_ID"],
        client_secret=config["ADCGen1Client"]["CLIENT_SECRET"]
    )

    # Need to update the resource we're authenticating against
    auth.data.update({"resource": "https://api.azuredatacatalog.com"})

    search_uri = SearchURI(catalog_name, api_version)

    output = []
    total_iter = 0
    while(True):
        results = requests.get(
            search_uri.uri,
            headers=auth.get_authentication_headers()
        )
        content = results.json()
        output.extend(content.get("results", []))
        if (content.get("totalResults", 0) >= len(output)) or total_iter > max_iter:
            break
        else:
            search_uri.add_page()
        total_iter = total_iter + 1

    return output


if __name__ == "__main__":
    """
    The defaults assume that you are running this from samples/migrateADCGen1.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", default="./config.ini")
    parser.add_argument("--assets")
    parser.add_argument("--terms")
    args, _ = parser.parse_known_args()

    gt = GuidTracker()

    config = configparser.ConfigParser()
    config.read(args.config)

    with open(args.terms, 'r') as fp:
        terms = json.load(fp)
        termMapping = {t["id"]: t["name"]+"@Glossary" for t in terms}

    adc_assets = []
    if args.assets:
        with open(args.assets, 'r') as fp:
            adc_assets = json.load(fp)
    else:
        adc_assets = download_gen1_assets(config, count=1)

    
    oauth = ServicePrincipalAuthentication(
        tenant_id=config["PurviewClient"]["TENANT_ID"],
        client_id=config["PurviewClient"]["CLIENT_ID"],
        client_secret=config["PurviewClient"]["CLIENT_SECRET"]
    )
    client = PurviewClient(
        account_name=config["PurviewClient"]["PURVIEW_ACCOUNT_NAME"],
        authentication=oauth
    )

    mappers = []
    for asset in adc_assets:
        try:
            mapper = AssetFactory.map_asset(asset, termMapping)
            mappers.append(mapper)
        except ValueError as e:
            print(e)
        
    print(f"Started with {len(adc_assets)} and ended up with {len(mappers)} processed.")

    for mapper in mappers:
        print(f"Working on: {mapper.qualified_name()}")
        if mapper.experts:
            mapper.experts = ["f2149281-20da-4c27-89c6-75597a1235b1"]  
        # Handles
        # experts
        # friendlyName
        # description      
        try:
            results = client.upload_entities([mapper.entity("-1")])
            # Handles
            ## glossary terms
            for rel in mapper.glossary_entity_relationships():
                try:
                    client.upload_relationship(rel)
                except AtlasException:
                    print("\tSkipping table glossary relationship since it likely exists")
            
            # Handles glossary terms at the column level
            for col_rel in mapper.glossary_column_relationships():
                try:
                    print(col_rel)
                    client.upload_relationship(col_rel)
                except:
                    print("\tSkipping column glossary relationship since it likely exists")
            
            # Handles column level updates
            for col_upd in mapper.partial_column_updates():
                print(col_upd)
                client.partial_update_entity(
                    typeName=col_upd["typeName"],
                    qualifiedName=col_upd["qualifiedName"],
                    attributes = col_upd["attributes"]
                )
        except Exception as e:
            print(f"FAILED DURING {mapper.qualified_name()}")
            print(e)
            print("CONTINUING TO PROCESS...")
