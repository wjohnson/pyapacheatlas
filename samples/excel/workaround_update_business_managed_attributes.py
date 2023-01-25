import json
import os

from openpyxl import load_workbook

# PyApacheAtlas packages
# Connect to Atlas via a Service Principal
from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient  # Communicate with your Atlas server
from pyapacheatlas.readers import ExcelConfiguration, ExcelReader

if __name__ == "__main__":
    """
    This sample provides a workaround to read a custom excel template
    """

    # Authenticate against your Atlas server
    cred = ServicePrincipalAuthentication(
        tenant_id=os.environ.get("TENANT_ID", ""),
        client_id=os.environ.get("CLIENT_ID", ""),
        client_secret=os.environ.get("CLIENT_SECRET", "")
    )
    # Alternatively, use Azure CLI Credential
    # from azure.identity import AzureCliCredential
    # cred = AzureCliCredential()
    client = PurviewClient(
        account_name = os.environ.get("PURVIEW_NAME", ""),
        authentication=cred
    )

    # Update these values to reflect your excel file
    file_path = "./PATH_TO_EXCEL.xlsx"
    sheet_name = "sheet1"

    excel_config = ExcelConfiguration()
    excel_reader = ExcelReader(excel_config)
    wb = load_workbook(file_path)

    rows = excel_reader._parse_spreadsheet(wb[sheet_name])
    
    # Assume the excel file has a guid and managed attribute column (attributeName)
    for row in rows:
        try:
            results = client.update_businessMetadata(
                guid=row["guid"],
                businessMetadata={"groupOrTypeName": {"attributeName":row["attributeName"]}}
            )
        except Exception as e:
            print(row)
            raise e
    
    # Assuming you have qualifiedName, typeName, and managed attribute column (attributeName)
    # This would be useful if you don't know the guids of your asset
    # This could be made more efficient by calling get_entity for all rows with the same typename
    # it would require sorting your rows by typeName and providing a list of qualified names to get_entity

    # for row in rows:
    #     try:
    #         response = client.get_entity(
    #             qualifiedName=row["qualifiedName"],
    #             typeName=row["typeName"]
    #         )
    #         if len(response["entities"]) == 0:
    #             print(f"Not found, skipping: {row}")
            
    #         single_entity = response["entities"][0]
    #         results = client.update_businessMetadata(
    #             guid=single_entity["guid"],
    #             businessMetadata={"groupOrTypeName": {"attributeName":row["attributeName"]}}
    #         )
    #     except Exception as e:
    #         print(row)
    #         raise e

    print("Completed bulk update of managed attributes.")
