import json
import os

from openpyxl import Workbook
from openpyxl import load_workbook

# PyApacheAtlas packages
# Connect to Atlas via a Service Principal
from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient  # Communicate with your Atlas server
from pyapacheatlas.readers import ExcelConfiguration, ExcelReader

if __name__ == "__main__":
    """
    This sample provides an end to end example of reading an excel file
    that organizes a set of terms and entities to be combined with
    additional processing. The code below demonstrates the full process
    of parsing the sheet, looking up the entities, merging entities
    and terms, and finally assigning the terms to the entities.

    You'll need to provide a spreadsheet with a tab called AssignTerms
    that has columns typeName, qualifiedName, and term.

    The term should be the term's formal name. The typeName should be the
    Atlas type name and not the friendly display name. The qualified name
    should be the fully qualified name of the entity you want to assign
    the given row's term with.
    """

    # Authenticate against your Atlas server
    oauth = ServicePrincipalAuthentication(
        tenant_id=os.environ.get("TENANT_ID", ""),
        client_id=os.environ.get("CLIENT_ID", ""),
        client_secret=os.environ.get("CLIENT_SECRET", "")
    )
    client = PurviewClient(
        account_name = os.environ.get("PURVIEW_NAME", ""),
        authentication=oauth
    )

    res = client.glossary.get_glossary()
    print(res)

    # SETUP: This is just setting up the excel file for you
    file_path = "./withterms.xlsx"
    excel_config = ExcelConfiguration()
    excel_reader = ExcelReader(excel_config)

    # ACTUAL WORK: This parses our excel file and organizes the entities both
    # by the type of entity (more efficient for looking up the unique id) and
    # by the term (more efficient for assigning multiple entities to one term).
    entities_by_type, entities_by_term = excel_reader.parse_assign_terms(file_path)

    qn_to_guid = {}
    # For every type referenced in the spreadsheet, look up the entity using
    # the provided qualifiedNames all at once
    for typeName in entities_by_type:
        print(f"Working on type: {typeName}")
        qualifiedNames = entities_by_type[typeName]
        entity_resp = client.get_entity(qualifiedName=qualifiedNames, typeName=typeName)
        # From the response, extract all the qualified names and their guids to
        # create a lookup table.
        _local_qn_to_guid = {e["attributes"]["qualifiedName"]:e["guid"] for e in entity_resp["entities"]}
        # A bit of error handling to make sure we didn't miss an entity
        # If this exception occurs, check your qualified name and type in
        # the spreadsheet.
        if len(_local_qn_to_guid) != len(qualifiedNames):
            raise RuntimeError("Some qualified names were not found: {}".format(
                set(qualifiedNames).difference(qn_to_guid.keys())))
        # Add these entities to our main lookup table
        qn_to_guid.update(_local_qn_to_guid)

    # We need the default glossary and its guid to make assigning terms more
    # efficient.
    default_glossary = client.glossary.get_glossary()

    # For every term referenced in the spreadsheet, lookup the associated
    # entities from the lookup table we just made, then attempt to assign the
    # term to the entities.
    for term in entities_by_term:
        print(f"Working on term: {term}")
        entities_to_assign = [{"guid":qn_to_guid[e]} for e in entities_by_term[term]]
        _ = client.glossary.assignTerm(
            entities=entities_to_assign, termName=term,
            glossary_guid=default_glossary["guid"]
            )

    # If the program made it this far without error, we've succeeded!
    print("Completed term assignments from Excel file.")
