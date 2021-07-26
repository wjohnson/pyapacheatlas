import argparse
import configparser
import csv
import json
import time
import os

import requests

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core.client import PurviewClient


def download_gen1_terms(config):
    catalog_name = config["ADCGen1Client"]["CATALOG_NAME"]
    glossary_name = config["ADCGen1Client"]["GLOSSARY_NAME"]
    api_version = "2016-03-30"

    auth = ServicePrincipalAuthentication(
        tenant_id=config["ADCGen1Client"]["TENANT_ID"],
        client_id=config["ADCGen1Client"]["CLIENT_ID"],
        client_secret=config["ADCGen1Client"]["CLIENT_SECRET"]
    )

    # Need to update the resource we're authenticating against
    auth.data.update({"resource": "https://api.azuredatacatalog.com"})

    # This endpoint provides you with all glossary terms in ADC Gen1
    enumerate_uri = f"https://api.azuredatacatalog.com/catalogs/{catalog_name}/glossaries/{glossary_name}/terms?api-version={api_version}"

    output = []
    while(True):
        results = requests.get(
            enumerate_uri,
            headers=auth.get_authentication_headers()
        )
        content = results.json()
        output.extend(content["value"])
        if "nextLink" not in content:
            break
        else:
            enumerate_uri = content["nextLink"]

    with open(config["Default"]["ADCTermsPath"], 'w') as fp:
        json.dump(output, fp, indent=1)

    return output


def convert_gen1_to_purview_terms(config):
    adc_terms_path = config["Default"]["ADCTermsPath"]
    purview_import_path = config["Default"]["PurviewImportPath"]
    with open(adc_terms_path, 'r') as fp:
        adc_terms = json.load(fp)

    output = []
    term_id_to_name = {}
    # Expecting:Name,Definition,Status,Related Terms,Synonyms,Acronym,Experts,Stewards
    for term in adc_terms:
        term_id_to_name.update({term["id"]: term["name"]})
        output.append(
            {
                "name": term["name"],
                "status": "Approved",  # Defaulting to Approved
                # May want term["description"] instead?
                "definition": term["definition"],
                "acronyms": "",
                "resources": "",
                "related_term": term.get("parentId", ""),
                "synonyms": "",
                "stewards": ';'.join([s["upn"] for s in term["stakeholders"]]),
                "experts": ""
            }
        )

    with open(config["Default"]["PurviewImportPath"], 'w', newline='',
              encoding='utf-8') as fp:
        importwriter = csv.writer(fp, quoting=csv.QUOTE_ALL, quotechar='"',
                                  lineterminator='\n')
        # Write Header with no quotes
        fp.write(
            "Name,Status,Definition,Acronym,Resources,Related Terms,Synonyms,Stewards,Experts\n"
        )

        for row in output:
            # Update the related term if it exists
            if row["related_term"] != "":
                row["related_term"] = term_id_to_name[row["related_term"]]
            importwriter.writerow(list(row.values()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--download-only", action="store_true", default=False)
    parser.add_argument("--config", default="./samples/migrateADCGen1/config.ini")
    args, _ = parser.parse_known_args()

    config = configparser.ConfigParser()
    config.read(args.config)

    # Configure your Purview Authentication
    oauth = ServicePrincipalAuthentication(
        tenant_id=config["PurviewClient"]["TENANT_ID"],
        client_id=config["PurviewClient"]["CLIENT_ID"],
        client_secret=config["PurviewClient"]["CLIENT_SECRET"]
    )
    client = PurviewClient(
        account_name=config["PurviewClient"]["PURVIEW_ACCOUNT_NAME"],
        authentication=oauth
    )

    # Download the Gen 1 Terms to a json document
    print("Downloading ADC Gen 1 Terms...")
    download_gen1_terms(config)
    print("Successfully downloaded ADC Gen 1 Terms.")

    if args.download_only:
        exit()

    # Convert the json to a csv for import
    print("Converting ADC Gen 1 Terms to be CSV for Purview Upload...")
    convert_gen1_to_purview_terms(config)


    print("Beginning upload of terms to Purview.")
    # Call the import terms method to take the csv and upload it
    results = client.import_terms(config["Default"]["PurviewImportPath"])

    print("Initial Upload Status:")
    print(json.dumps(results, indent=2))

    print("Checking Status every Five Seconds until status != 'Running'")
    while(True):
        ops_status = client.import_terms_status(results["id"])
        print(json.dumps(ops_status, indent=2))
        if ops_status["status"] != "RUNNING":
            break
        time.sleep(5)
