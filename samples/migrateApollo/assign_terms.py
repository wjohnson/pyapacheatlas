import argparse
import json
import os
import sys

import openpyxl

from pyapacheatlas.core import AtlasClient
from pyapacheatlas.auth import ServicePrincipalAuthentication


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file-path",
                        help="The path to the Apollo export.")
    parser.add_argument(
        "--sheetname",
        help="The name of the sheet to pull data out of for the given file-path.")
    args = parser.parse_args()

    # Authenticate against your Atlas server
    oauth = ServicePrincipalAuthentication(
        tenant_id=os.environ.get("TENANT_ID", ""),
        client_id=os.environ.get("CLIENT_ID", ""),
        client_secret=os.environ.get("CLIENT_SECRET", "")
    )
    atlas_client = AtlasClient(
        endpoint_url=os.environ.get("ENDPOINT_URL", ""),
        authentication=oauth
    )

    # Read in the args.file_path
    wb = openpyxl.load_workbook(args.file_path)
    required_sheet = wb.sheetnames[0]
    # Read the header of the args.sheetname
    # Otherwise, get the first sheet
    if args.sheetname:
        required_sheet = args.sheetname

    data_sheet = wb.get_sheet_by_name(required_sheet)

    # Iterate over each row, could do this in pandas but want to avoid
    # the dependency

    # Getting the headers
    sheet_headers = []
    null_threshold = 0.5
    for row in data_sheet.iter_rows(min_row=1, max_col=data_sheet.max_column, max_row=1):
        for idx, cell in enumerate(row):
            sheet_headers.append(cell.value)

    sheet_data = []
    for row in data_sheet.iter_rows(min_row=2, max_col=data_sheet.max_column,
                                    max_row=data_sheet.max_row + 1):
        row_data = {}
        nulls = 0
        for idx, cell in enumerate(row):
            row_data[sheet_headers[idx]] = cell.value
            if cell.value is None:
                nulls = nulls + 1
        
        if float(nulls) / float(len(row_data)) < null_threshold:
            sheet_data.append(row_data)

    # Extract the following fields:
    key_headers = [
        "fld_it_name", "fld_business_name",
        "tbl_it_name", "tbl_business_name"
    ]

    # Find the unique terms (*_business_name)
    term_guids = dict()
    known_entities = set()
    # TODO: Find the qualifiedName for the table and column
    for row in sheet_data:
        table_term = row["tbl_business_name"]
        column_term = row["fld_business_name"]
        table_name = row["tbl_it_name"]
        column_name = row["fld_it_name"]

        known_entities.add(table_name)
        known_entities.add(column_name)
        
        if table_term not in term_guids:
            term_guids[table_term] = {"guid":None, "qualifiedNames":set()}
        if column_term not in term_guids:
            term_guids[column_term] = {"guid":None, "qualifiedNames":set()}
        
        term_guids[table_term]["qualifiedNames"].add(table_name)
        term_guids[column_term]["qualifiedNames"].add(column_name)
    
    
    # Look up the terms necessary
    glossary = atlas_client.get_glossary()

    for term in glossary["terms"]:
        current_term_value = term["displayText"]
        if current_term_value in term_guids:
            term_guids[current_term_value]["guid"] = term["termGuid"]
    

    for term in term_guids:
        term_guids[term]["qualifiedNames"] = list(term_guids[term]["qualifiedNames"])
    
    print(json.dumps(term_guids))
    
    print(len(term_guids))

    # TODO: Flesh out the search query loop
    # For each column and table, find their entity id
    # qualified_name_lookup = dict()
    # for qualifiedName in known_entities:
    #     search_results = atlas_client.search_entities(query=qualifiedName)
    #     for batch in search_results:
    #         for entity in batch:
    #             if entity["qualifiedName"] == qualifiedName:
    #                 qualified_name_lookup[qualifiedName] = entity["guid"]
    #                 break
    #         if qualifiedName in qualified_name_lookup:
    #             break
    
    # TODO: Create the relationship between term_guids and the entities
    # for term in term_guids:
    #     for qualified_name in term["qualifiedNames"]:
    #         if qualified_name not in qualified_name_lookup:
    #             print(f"Warning: {qualified_name} was not found in any entities in the catalog.")
    #             break
    #         entity_guid = qualified_name_lookup[qualified_name]
    #         # TODO: Define a relationship
    #         relationship = {}
    #         try:
    #             atlas_client.upload_relationship(relationship)
    #         except Exception as e:
    #             print(f"Exception for {term}:{qualified_name} and was not uploaded: {e}")
        


            
                

