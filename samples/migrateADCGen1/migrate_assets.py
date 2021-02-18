import configparser
import csv
import json
import time
import os

import requests

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core.client import PurviewClient

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
            f"https://api.azuredatacatalog.com/catalogs/{self.catalog_name}"+
            f"/search/search?api-version={self.api_version}&"+
            f"searchTerms={self.search_terms}&startPage={self.start_page}&"+
            f"count={self.count}&view=DataSource"
        )
        return output_uri
    
    def add_page(self):
        self.start_page = self.start_page + 1


def download_gen1_assets(config, search_terms = "*", count=100, max_iter = 1000):
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

    # This endpoint provides you with all glossary terms in ADC Gen1

    search_uri = SearchURI(catalog_name, api_version)

    #search_uri = f"https://api.azuredatacatalog.com/catalogs/{catalog_name}/search/search?api-version={api_version}&searchTerms={search_terms}&startPage={start_page}&count={count}&view=DataSource"

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
    config = configparser.ConfigParser()
    config.read("./samples/migrateADCGen1/config.ini")

    # Configure your Purview Authentication
    # oauth = ServicePrincipalAuthentication(
    #     tenant_id=config["PurviewClient"]["TENANT_ID"],
    #     client_id=config["PurviewClient"]["CLIENT_ID"],
    #     client_secret=config["PurviewClient"]["CLIENT_SECRET"]
    # )
    # client = PurviewClient(
    #     account_name=config["PurviewClient"]["PURVIEW_ACCOUNT_NAME"],
    #     authentication=oauth
    # )

    # Download the Gen 1 Terms to a json document
    results = download_gen1_assets(config, count=1)
    
    print(json.dumps(results, indent=2))
