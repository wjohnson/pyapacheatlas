import warnings

class AtlasEntity():
    """
    A python representation of the AtlasEntity from Apache Atlas.
    """

    def __init__(self, name, typeName, qualified_name, guid=None, **kwargs):
        """
        :param str name: The name of this instance of an atlas entity.
        :param str typeName: The type this entity should be.
        :param str qualified_name: The unique "qualified name" of this
            instance of an atlas entity.
        :param Union(str,int), optional guid:
            The guid to reference this entity by.
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
        self.attributes.update({"name": None, "qualifiedName": None})
        self.name = name
        self.qualifiedName = qualified_name
        if "description" in kwargs:
            self.attributes.update({"description": kwargs["description"]})
        self.relationshipAttributes = kwargs.get("relationshipAttributes", {})
        self.classifications = kwargs.get("classifications", [])

    def __eq__(self, other):
        return self.qualifiedName == other

    def __hash__(self):
        return hash(self.qualifiedName)

    def __ne__(self, other):
        return self.qualifiedName != other

    def __repr__(self):
        return "AtlasEntity({type_name},{qual_name})".format(
            type_name=self.typeName,
            qual_name=self.qualifiedName
        )

    def __str__(self):
        return "AtlasEntity({type_name},{qual_name})".format(
            type_name=self.typeName,
            qual_name=self.qualifiedName
        )

    @property
    def name(self):
        """
        Retrieve the name of this entity.

        :return: The name of the entity.
        :rtype: str
        """
        return self.attributes["name"]
    
    @name.setter
    def name(self, value):
        """
        Set the name of this entity.

        :param str value: The name of the entity.
        """
        self.attributes["name"] = value
    
    @property
    def qualifiedName(self):
        """
        Retrieve the qualifiedName of this entity.

        :return: The name of the entity.
        :rtype: str
        """
        return self.attributes["qualifiedName"]
    
    @qualifiedName.setter
    def qualifiedName(self, value):
        """
        Set the qualifiedName of this entity.

        :param str value: The qualifiedName of the entity.
        """
        self.attributes["qualifiedName"] = value

    def get_name(self):
        """
        Deprecated in favor of .name property.
        Retrieve the name of this entity.

        :return: The name of the entity.
        :rtype: str
        """
        warnings.warn("Get name using AtlasEntity.name.", 
            category=DeprecationWarning, stacklevel=2)
        return self.attributes["name"]

    def get_qualified_name(self):
        """
        Deprecated in favor of .qualifiedName.
        Retrieve the qualified (unique) name of this entity.

        :return: The qualified name of the entity.
        :rtype: str
        """
        warnings.warn("Get qualified name using AtlasEntity.qualifiedName.", 
            category=DeprecationWarning, stacklevel=2)
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
            # Add ins for optional top level attributes
            if len(self.classifications) > 0:
                output.update({"classifications": self.classifications})

        return output

    def merge(self, other):
        if self.qualifiedName != other.qualifiedName:
            raise TypeError("Type:{} cannot be merged with {}".format(
                type(other), type(self)))

        # Take the "earlier" defined entity's guid
        self.guid = other.guid
        # Add attributes that are not present in the later row's attributes
        # Meaning, later attributes SUPERCEDE attributes
        # This helps with updating input and output attributes
        # later in process entities.
        _other_attr_keys = set(other.attributes.keys())
        _self_attr_keys = set(self.attributes.keys())
        _new_keys_in_other = _other_attr_keys.difference(_self_attr_keys)
        self.attributes.update(
            {k: v for k, v in other.attributes.items()
                if k in _new_keys_in_other})
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
    :param inputs:
        The list of input entities expressed as dicts and in minimum
        format (guid, type name, qualified name) or an AtlasEntity.
    :type inputs: Union[list(dict), :class:`pyapacheatlas.core.entity.EntityDef`]
    :param outputs:
        The list of output entities expressed as dicts and in minimum format
        (guid, type name, qualified name) or an AtlasEntity.
    :type outputs: Union[list(dict), :class:`pyapacheatlas.core.entity.EntityDef`]
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
        self.attributes.update({"inputs": None, "outputs": None})
        self.inputs = inputs
        self.outputs = outputs
    
    def _parse_atlas_entity(self, iterable):
        """
        :param iterable: An iterable of dict or AtlasEntity
        """
        return [
                e.to_json(minimum=True)
                if isinstance(e, AtlasEntity)
                else e
                for e in iterable
            ]

    @property
    def inputs(self):
        return self.attributes.get("inputs")

    @inputs.setter
    def inputs(self, value):
        # TODO: Consider checking if there is a valid guid to return a simpler min
        if value is not None:
            self.attributes["inputs"] = self._parse_atlas_entity(value)
        else:
            self.attributes["inputs"] = None

    @property
    def outputs(self):
        return self.attributes.get("outputs")

    @outputs.setter
    def outputs(self, value):
        # TODO: Consider checking if there is a valid guid to return a simpler min
        if value is not None:
            self.attributes["outputs"] = self._parse_atlas_entity(value)
        else:
            self.attributes["outputs"] = None
    
    def addInput(self, *args):
        """
        Add one or many entities to the inputs.

        :param args:
            The atlas entities you are adding. They are comma delimited dicts
            or AtlasEntity. You can expand a list with `*my_list`.
        :type args: Union[dict, :class:`pyapacheatlas.core.entity.AtlasEntity`]
        """
        self.inputs = self.inputs + self._parse_atlas_entity(args)

    def addOutput(self, *args):
        """
        Add one or many entities to the outputs.

        :param args:
            The atlas entities you are adding. They are comma delimited dicts
            or AtlasEntity. You can expand a list with `*my_list`.
        :type args: Union[dict, :class:`pyapacheatlas.core.entity.AtlasEntity`]
        """
        self.outputs = self.outputs + self._parse_atlas_entity(args)

    def merge(self, other):
        """
        Combine the inputs and outputs of a process. Fails if one side has a
        null input or output. Updates the object that merge is called on.
        """
        super().merge(other)
        # Requires that the input and output attributes have
        # not been altered on self.
        _combined_inputs = self.inputs + other.inputs
        _combined_outputs = self.outputs + other.outputs

        _deduped_inputs = [dict(t) for t in set(
            tuple(d.items()) for d in _combined_inputs)]
        _deduped_outputs = [dict(t) for t in set(
            tuple(d.items()) for d in _combined_outputs)]
        self.inputs = _deduped_inputs
        self.outputs = _deduped_outputs

    def set_inputs(self, inputs):
        """
        Deprecated: Use AtlasEntity.inputs to set inputs.
        Set the inputs to the process.  Inputs should be AtlasEntity minimum
        json of `{qualifiedName:..., guid:..., typeName:...}`.

        :param list(dict) inputs: The minimum json inputs.
        """
        warnings.warn("Set inputs using AtlasProcess.inputs = ...", category=DeprecationWarning, stacklevel=2)
        self.attributes["inputs"] = inputs

    def set_outputs(self, outputs):
        """
        Deprecated: Use AtlasEntity.outputs to set outputs.
        Set the outputs to the process.  Outputs should be AtlasEntity minimum
        json of `{qualifiedName:..., guid:..., typeName:...}`.

        :param list(dict) outputs: The minimum json outputs.
        """
        warnings.warn("Set outputs using AtlasProcess.outputs = ...", category=DeprecationWarning, stacklevel=2)
        self.attributes["outputs"] = outputs

    def get_inputs(self):
        """
        Deprecated: Use AtlasEntity.inputs to get inputs.
        Return the inputs to the process.

        :return: The minimum json inputs.
        :rtype: list(dict)
        """
        warnings.warn("Get inputs using AtlasProcess.inputs.", category=DeprecationWarning, stacklevel=2)
        return self.attributes.get("inputs")

    def get_outputs(self):
        """
        Deprecated: Use AtlasEntity.outputs to set outputs.
        Set the outputs to the process.

        :return: The minimum json inputs.
        :rtype: list(dict)
        """
        warnings.warn("Get outputs using AtlasProcess.outputs.", category=DeprecationWarning, stacklevel=2)
        return self.attributes.get("outputs")

class AtlasClassification():
    """
    A python implementation of the AtlasClassification from Apache Atlas.
    """

    def __init__(self, typeName, entityStatus = "ACTIVE", propagate=False,
        removePropagationsOnEntityDelete = False, **kwargs):
        """
        :param str typeName: The name of this classification.
        :param str entityStatus: One of ACTIVE, DELETED, PURGED.
        :param str qualified_name: The unique "qualified name" of this
            instance of an atlas entity.
        :param Union(str,int), optional guid:
            The guid to reference this entity by.
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
        if entityStatus not in ["ACTIVE", "PURGED", "DELETED"]:
            raise ValueError(f"entityStatus must be one of ACTIVE, PURGED, or DELETED.")
        self.typeName = typeName
        self.entityStatus = entityStatus
        self.propagate = propagate
        self.removePropagationsOnEntityDelete = removePropagationsOnEntityDelete
        self.attributes = kwargs.get("attributes", {})
        self.validityPeriods = kwargs.get("validityPeriods", [])

    def __repr__(self):
        return "AtlasClassification({type_name})".format(
            type_name=self.typeName
        )

    def __str__(self):
        return "AtlasClassification({type_name})".format(
            type_name=self.typeName
        )

    def to_json(self):
        """
        Convert this atlas entity to a dict / json.

        :param bool minimum: If True, returns only the
            type name, qualified name, and guid of the entity.  Useful
            for being referenced in other entities like process inputs
            and outputs.
        :return: The json representation of this atlas entity.
        :rtype: dict
        """

        output = {
            "typeName":self.typeName,
            "entityStatus":self.entityStatus,
            "propagate":self.propagate,
            "removePropagationsOnEntityDelete": self.removePropagationsOnEntityDelete,
            "validityPeriods":self.validityPeriods,
            "attributes":self.attributes
        }
        return output
