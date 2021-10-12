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
    This sample provides an end to end example of reading an excel file,
    that organizes and assigns terms to entities.
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

    # ACTUAL WORK: This parses our excel file and creates a batch to upload
    entities_by_type, entities_by_term = excel_reader.parse_assign_terms(file_path)

    qn_to_guid = {}
    for typeName in entities_by_type:
        qualifiedNames = entities_by_type[typeName]
        entity_resp = client.get_entity(qualifiedName=qualifiedNames, typeName=typeName)
        _local_qn_to_guid = {e["attributes"]["qualifiedName"]:e["guid"] for e in entity_resp["entities"]}
        if len(_local_qn_to_guid) != len(qualifiedNames):
            raise RuntimeError("Some qualified names were not found: {}".format(
                set(qualifiedNames).difference(qn_to_guid.keys())))
        qn_to_guid.update(_local_qn_to_guid)
    
    default_glossary = client.glossary.get_glossary()

    for term in entities_by_term:
        entities_to_assign = [{"guid":qn_to_guid[e]} for e in entities_by_term[term]]
        _ = client.glossary.assignTerm(
            entities=entities_to_assign, termName=term,
            glossary_guid=default_glossary["guid"]
            )

    print("Completed term assignments from Excel file.")
