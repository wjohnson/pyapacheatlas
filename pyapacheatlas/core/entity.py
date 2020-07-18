class AtlasEntity():
    """
    A python representation of the AtlasEntity from Apache Atlas.
    """

    def __init__(self, name, typeName, qualified_name, guid = None, **kwargs):
        """
        :param str name: The name of this instance of an atlas entity.
        :param str typeName: The type this entity should be.
        :param str qualified_name: The unique "qualified name" of this 
            instance of an atlas entity.
        :param Union(str,int), optional guid: The guid to reference this entity by.
        :param dict relationshipAttributes: The relationship attributes
            representing how this entity is connected to others.  Commonly
            used for "columns" to indicate entity is a column of a table or
            "query" to indicate a process entity is tied another process in
            a column lineage scenario.
        :param dict, optional attributes: Additional attributes that your
            atlas entity may require.
        :param dict, optional classifications: Classifications that may
            be applied to this atlas entity.
        """
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
        self.classifications = kwargs.get("classifications", {})
    
    def get_name(self):
        """
        Retrieve the name of this entity.

        :return: The name of the entity.
        :rtype: str
        """
        return self.attributes["name"]

    def get_qualified_name(self):
        """
        Retrieve the qualified (unique) name of this entity.
        
        :return: The qualified name of the entity.
        :rtype: str
        """
        return self.attributes["qualifiedName"]

    def to_json(self, minimum=False):
        """
        Convert this atlas entity to a dict / json.
        
        :param bool minimum: If True, returns only the
            type name, qualified name, and guid of the entity.  Useful
            for being referenced in other entities like process inputs
            and outputs.
        :return: The json representation of this atlas entity.
        :rtype: dict
        """
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
    """
    A subclass of AtlasEntity that forces you to include the inputs and
    outputs of the process.

    :param str name: The name of this instance of an atlas entity.
    :param str typeName: The type this entity should be.
    :param str qualified_name: The unique "qualified name" of this 
        instance of an atlas entity.
    :param list(dict) inputs: The list of input entities expressed as dicts
        and in minimum format (guid, type name, qualified name).
    :param list(dict) outputs: The list of output entities expressed as dicts
        and in minimum format (guid, type name, qualified name).
    :param Union(str,int), optional guid: The guid to reference this entity by.
    :param dict relationshipAttributes: The relationship attributes
        representing how this entity is connected to others.  Commonly
        used for "columns" to indicate entity is a column of a table or
        "query" to indicate a process entity is tied another process in
        a column lineage scenario.
    :param dict, optional attributes: Additional attributes that your
        atlas entity may require.
    :param dict, optional classifications: Classifications that may
        be applied to this atlas entity.
    """

    def __init__(self, name, typeName, qualified_name, inputs, outputs, guid=None, **kwargs):
        super().__init__(name, typeName, qualified_name, guid=guid, **kwargs)
        self.attributes.update({"inputs": inputs, "outputs": outputs})