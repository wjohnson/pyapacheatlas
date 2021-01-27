import argparse
import configparser
import csv
import json

from pyapacheatlas.auth import ServicePrincipalAuthentication


def convert_gen1_to_purview_terms(config):
    adc_terms_path = config["Default"]["ADCTermsPath"]
    purview_import_path = config["Default"]["PurviewImportPath"]
    with open(adc_terms_path, 'r') as fp:
        adc_terms = json.load(fp)
    
    output = []
    term_id_to_name  = {}
    # Expecting:Name,Definition,Status,Related Terms,Synonyms,Acronym,Experts,Stewards
    for term in adc_terms:
        term_id_to_name.update({term["id"]:term["name"]})
        output.append(
            {
            "name": term["name"],
            "definition": term["definition"], # May want term["description"] instead?
            "status": "ACTIVE", # Defaulting to Active
            "related_term": term.get("parentId", ""),
            "synonyms":"",
            "acronyms":"",
            "experts":';'.join([s["upn"] for s in term["stakeholders"]]),
            "stewards":""
            }
        )

    with open(config["Default"]["PurviewImportPath"], 'w', newline='') as fp:
        importwriter = csv.writer(fp)
        for row in output:
            # Update the related term if it exists
            if row["related_term"] != "":
                row["related_term"] = term_id_to_name[row["related_term"]]
            importwriter.writerow( list(row.values()) )


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("./samples/migrateADCGen1/config.ini")
    convert_gen1_to_purview_terms(config)