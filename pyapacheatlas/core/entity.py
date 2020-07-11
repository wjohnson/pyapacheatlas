class AtlasEntity():

    def __init__(self, name, typeName, qualified_name, guid = None, **kwargs):
        super().__init__()
        self.typeName = typeName
        self.guid = guid
        self.attributes = kwargs.get("attributes", {})
        self.attributes.update({"name": name, "qualifiedName": qualified_name})
        # Example Relationship Attribute
        # {"relationshipName": {
        #   "qualifiedName": "",
        #   "guid": "",
        #   "typeName": ""
        # }}
        self.relationshipAttributes = kwargs.get("relationshipAttributes", {})
    
    def to_json(self, minimum=False):
        if minimum:
            output = {
                "typeName": self.typeName,
                "guid": self.guid,
                "qualifiedName": self.attributes["qualifiedName"]
            }
        else:
            output = {
                "typeName": self.typeName,
                "guid": self.guid,
                "attributes": self.attributes,
                "relationshipAttributes": self.relationshipAttributes
            }
        return output

class AtlasProcess(AtlasEntity):

    def __init__(self, name, typeName, qualified_name, inputs, outputs, guid=None, **kwargs):
        super().__init__(name, typeName, qualified_name, guid=guid, **kwargs)
        self.attributes.update({"inputs": inputs, "outputs": outputs})