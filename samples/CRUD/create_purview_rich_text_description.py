import json

# PyApacheAtlas packages
# Connect to Atlas via the Azure CLI
from azure.identity import AzureCliCredential
from pyapacheatlas.core import PurviewClient, AtlasEntity

if __name__ == "__main__":
    """
    This sample provides an example of creating an entity with a rich text description.

    This is only available in Microsoft Purview. Rich text is made available using the
    userDescription attribute and the microsoft_isDescriptionRichText CUSTOM attribute.

    You must use both attribute and customAttribute to enable this feature in the UI.
    """

    # Authenticate 
    cred = AzureCliCredential()
    client = PurviewClient(
        account_name = "PURVIEW_SERVICE_NAME",
        authentication=cred
    )

    asset01 = AtlasEntity(
        name="input01",
        typeName="DataSet",
        qualified_name="pyapacheatlas://richtextasset",
        guid="-100",
        attributes={
            "userDescription": "<div><h3>Business Process</h3><p>This report shows the remaining shelf life of inventory of Finished Goods, semi-finished Goods, Raw and Packaging materials expressed in percentage in two different ways :</p> <p> <h1> New para </h1> </p>"
        },
        # This custom attribute flips a switch inside of the Purview UI to render
        # the rich text description.
        customAttributes={
            "microsoft_isDescriptionRichText": "true"
        }
    )
    
    # Convert the individual entities into json before uploading.
    results = client.upload_entities(
        batch=[asset01]
    )

    print(json.dumps(results, indent=2))
