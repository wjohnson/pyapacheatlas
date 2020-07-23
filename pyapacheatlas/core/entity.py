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
        self.classifications = kwargs.get("classifications", [])
    

    def __eq__(self, other):
        return self.get_qualified_name() == other.get_qualified_name()


    def __hash__(self):
        return hash(self.get_qualified_name())
    

    def __ne__(self, other):
        return self.get_qualified_name() != other.get_qualified_name()


    def __repr__(self):
        return "AtlasEntity({type_name},{qual_name})".format(
            type_name=self.typeName,
            qual_name=self.get_qualified_name()
        )


    def __str__(self):
        return "AtlasEntity({type_name},{qual_name})".format(
            type_name=self.typeName,
            qual_name=self.get_qualified_name()
        )


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
                "relationshipAttributes": self.relationshipAttributes,
                "classifications": self.classifications
            }
        return output
    
    def merge(self, other):
        if self.get_qualified_name() != other.get_qualified_name():
            raise TypeError("Type:{} cannot be merged with {}".format(type(other), type(self)))

        # Take the "earlier" defined entity's guid
        self.guid = other.guid
        # Add attributes that are not present in the later row's attributes
        # Meaning, later attributes SUPERCEDE attributes
        # This helps with updating input and output attributes later in process entities.
        _other_attr_keys = set(other.attributes.keys())
        _self_attr_keys = set(self.attributes.keys())
        _new_keys_in_other = _other_attr_keys.difference(_self_attr_keys)
        self.attributes.update({k:v for k,v in other.attributes.items() if k in _new_keys_in_other})
        # TODO: Handle duplicate classifications
        self.classifications.extend(other.classifications)

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
    
    def merge(self, other):
        super().merge(other)
        # Requires that the input and output attributes have not been altered on self.
        _combined_inputs = self.get_inputs()+other.get_inputs()
        _combined_outputs = self.get_outputs()+other.get_outputs()

        _deduped_inputs = [dict(t) for t in set(tuple(d.items()) for d in _combined_inputs)]
        _deduped_outputs = [dict(t) for t in set(tuple(d.items()) for d in _combined_outputs)]
        self.set_inputs(_deduped_inputs)
        self.set_outputs(_deduped_outputs)

    def set_inputs(self, inputs):
        """
        Set the inputs to the process.  Inputs should be AtlasEntity minimum 
        json of `{qualifiedName:..., guid:..., typeName:...}`.

        :param list(dict) inputs: The minimum json inputs.
        """
        self.attributes["inputs"] = inputs
    
    def set_outputs(self, outputs):
        """
        Set the outputs to the process.  Outputs should be AtlasEntity minimum 
        json of `{qualifiedName:..., guid:..., typeName:...}`.

        :param list(dict) outputs: The minimum json outputs.
        """
        self.attributes["outputs"] = outputs
    
    def get_inputs(self):
        """
        Return the inputs to the process.

        :return: The minimum json inputs.
        :rtype: list(dict)
        """
        return self.attributes["inputs"]
    
    def get_outputs(self):
        """
        Set the outputs to the process.

        :return: The minimum json inputs.
        :rtype: list(dict)
        """
        return self.attributes["outputs"]
    
