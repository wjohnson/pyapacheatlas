import warnings

class AtlasUnInit():
    """
    Represents a value that has not been initialized
    and will not be included in json body.
    """
    def __bool__(self):
        return False


class AtlasEntity():
    """
    A python representation of the AtlasEntity from Apache Atlas.

    :param str name: The name of this instance of an atlas entity.
    :param str typeName: The type this entity should be.
    :param str qualified_name: The unique "qualified name" of this
        instance of an atlas entity.
    :param Union(str,int) guid:
        The guid to reference this entity by. Should be a negative number
        if you're adding an entity. Consider using get_guid() method from
        :class:`~pyapacheatlas.core.util.GuidTracker` to retrieve unique
        negative numbers.
    :param dict, optional relationshipAttributes: The relationship attributes
        representing how this entity is connected to others.  Commonly
        used for "columns" to indicate entity is a column of a table or
        "query" to indicate a process entity is tied another process in
        a column lineage scenario.
    :param dict, optional attributes: Additional attributes that your
        atlas entity may require.
    :param dict, optional classifications: Classifications that may
        be applied to this atlas entity.
    :param dict(str, dict(str, list(dict(strt,str)))), optional contacts:
        Contacts should contain keys Experts and/or Owners. Their values should
        be a list of dicts with keys id and info. Id is a microsoft graph
        object id. Info is a string of extra information.
    """

    def __init__(self, name, typeName, qualified_name, guid=None, **kwargs):
        super().__init__()
        self.attributes = kwargs.get("attributes", {})
        self.attributes.update({"name": None, "qualifiedName": None})
        # Normally takes a dict of dicts
        self.businessAttributes = kwargs.get("businessAttributes", AtlasUnInit())
        self.classifications = kwargs.get("classifications", AtlasUnInit())
        # This isn't implemented in Apache Atlas, so being cautious
        # Data Structure: {"Expert":[{"id","info"}], "Owner":...}
        self.contacts = kwargs.get("contacts", AtlasUnInit())
        self.createTime = kwargs.get("createTime", AtlasUnInit())
        self.createdBy = kwargs.get("createdBy", AtlasUnInit())
        # Normally takes a dict of str
        self.customAttributes = kwargs.get("customAttributes", AtlasUnInit())
        self.guid = guid
        self.homeId = kwargs.get("homeId", AtlasUnInit())
        self.isIncomplete = kwargs.get("isIncomplete", AtlasUnInit())
        # Normally takes a list of strings
        self.labels = kwargs.get("labels", AtlasUnInit())
        self.lastModifiedTS = kwargs.get("lastModifiedTS", AtlasUnInit())
        self.provenanceType = kwargs.get("provenanceType", AtlasUnInit())
        self.proxy = kwargs.get("proxy", AtlasUnInit())
        self.relationshipAttributes = kwargs.get("relationshipAttributes", AtlasUnInit())
        self.source = kwargs.get("source", AtlasUnInit())
        self.sourceDetails = kwargs.get("sourceDetails", AtlasUnInit())
        self.status = kwargs.get("status", AtlasUnInit())
        self.typeName = typeName
        self.updateTime = kwargs.get("updateTime", AtlasUnInit())
        self.updatedBy = kwargs.get("updatedBy", AtlasUnInit())
        self.version = kwargs.get("version", AtlasUnInit())
        self.name = name
        self.qualifiedName = qualified_name
        if "description" in kwargs:
            self.attributes.update({"description": kwargs["description"]})
    
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

    def addBusinessAttribute(self, **kwargs):
        """
        Add one or many businessAttributes to the entity. This will
        also update an existing business attribute. You can pass in a parameter
        name and a dict.

        Kwargs:
            :param kwarg: The name(s) of the business attribute(s) you're adding.
            :type kwarg: dict
        """
        businessAttributes_was_uninitialized = isinstance(self.businessAttributes, AtlasUnInit)
        if businessAttributes_was_uninitialized:
            self.businessAttributes = {}
        try:
            self.businessAttributes.update(kwargs)
        except Exception as e:
            if businessAttributes_was_uninitialized:
                self.businessAttributes = AtlasUnInit()
            raise e
    
    def addClassification(self, *args):
        """
        Add one or many classifications to the entity. This will
        also update an existing attribute. You can pass in a parameter name and
        a string, an AtlasClassification, or a dictionary.

        :param args:
            The string, dictionary, or AtlasClassification passed as individual
            arguments. You can unpack a list using something like `*my_list`.
        :type args: Union(str, dict, :class:`~pyapacheatlas.core.entity.AtlasClassification`)
        """
        classification_was_uninitialized = isinstance(self.classifications, AtlasUnInit)
        classifications_to_add = []
        if classification_was_uninitialized:
            self.classifications = []
        try:
            for arg in args:
                if isinstance(arg, dict):
                    classifications_to_add.append(arg)
                elif isinstance(arg, str):
                    classifications_to_add.append(AtlasClassification(arg).to_json())
                elif isinstance(arg, AtlasClassification):
                    classifications_to_add.append(arg.to_json())
                else:
                    raise TypeError(
                        f"The type {type(arg)} for value {arg} can't be converted to a classification dict."
                    )
            # Made it through all the args, add the classifications
            self.classifications.extend(classifications_to_add)
        except Exception as e:
            if classification_was_uninitialized:
                self.classifications = AtlasUnInit()
            raise e

    
    def addCustomAttribute(self, **kwargs):
        """
        Add one or many customAttributes to the entity. This will
        also update an existing attribute. You can pass in a parameter name and
        a string.

        Kwargs:
            :param kwarg: The name(s) of the custom attribute(s) you're adding.
            :type kwarg: dict(str, str)
        """
        customAttributes_was_uninitialized = isinstance(self.customAttributes, AtlasUnInit)
        if customAttributes_was_uninitialized:
            self.customAttributes = {}
        try:
            self.customAttributes.update(kwargs)
        except Exception as e:
            if customAttributes_was_uninitialized:
                self.customAttributes = AtlasUnInit()
            raise e
    
    def addRelationship(self, **kwargs):
        """
        Add one or many relationshipAttributes to the entity. This will
        also update an existing relationship attribute. You can pass in a parameter
        name and then either an Atlas Entity, a dict representing an AtlasEntity,
        or a list containing dicts of AtlasEntity pointers. For example, you might
        pass in `addRelationship(table=AtlasEntity(...))` or
        `addRelationship(column=[{'guid':'abc-123-def`}])`.

        Kwargs:
            :param kwarg: The name of the relationship attribute you're adding.
            :type kwarg:
                Union(dict, :class:`pyapacheatlas.core.entity.AtlasEntity`)
        """
        relationshipAttributes_was_uninitialized = isinstance(self.customAttributes, AtlasUnInit)
        relationships_to_add = {}
        if relationshipAttributes_was_uninitialized:
            self.relationshipAttributes = {}
        try:
            for k,v in kwargs.items():
                val = v.to_json(minimum=True) if isinstance(v, AtlasEntity) else v
                relationships_to_add[k] = val
            # Add all the relationships
            self.relationshipAttributes.update(relationships_to_add)
        except Exception as e:
            if relationshipAttributes_was_uninitialized:
                self.relationshipAttributes = AtlasUnInit()


    def to_json(self, minimum=False):
        """
        Convert this atlas entity to a dict / json. Returns typename, guid,
        and qualified name if guid is not none. If guid is None then this will
        return typename, uniqueAttributes with a sub object of qualified name.

        By specifying a guid, this method assumes you will be uploading the
        entity (and want or at least willing to accept changes to the entity).
        By NOT specifying a guid, this assumes you will be using the entity as
        a reference used by another one in the upload (e.g. creating a process
        entity that uses an existing entity as an input or output).

        :param bool minimum: If True, returns only the
            type name, qualified name, and guid of the entity (when guid is
            defined). If True and guid is None, returns typeName,
            uniqueAttributes and qualifiedName. If False, return the full entity
            and its attributes and relationship attributes.
        :return: The json representation of this atlas entity.
        :rtype: dict
        """
        if minimum and self.guid is not None:
            output = {
                "typeName": self.typeName,
                "guid": self.guid,
                "qualifiedName": self.attributes["qualifiedName"]
            }
        elif minimum and self.guid is None:
            output = {
                "typeName": self.typeName,
                "uniqueAttributes": {
                    "qualifiedName": self.qualifiedName
                }
            }
        else:
            output = {
                "typeName": self.typeName,
                "guid": self.guid,
                "attributes": self.attributes
            }
            # Add ins for optional top level attributes
            for k, v in vars(self).items():
                is_uninitialized = isinstance(v, AtlasUnInit)
                is_asset_attribute = k in ["name", "qualifiedName"]
                if is_uninitialized or is_asset_attribute:
                    continue
                output[k] = v
        
        return output
    
    @classmethod
    def from_json(cls, entity_json):
        local_entity = entity_json.copy()
        guid = local_entity.pop("guid")
        typeName = local_entity.pop("typeName")
        name = local_entity["attributes"]["name"]
        qualified_name = local_entity["attributes"]["qualifiedName"]
        ae = cls(
            name = name,
            typeName= typeName,
            qualified_name = qualified_name,
            guid = guid,
            # This is necessary for AtlasProcess and shouldn't affect Entity
            inputs = local_entity["attributes"].get("inputs"),
            outputs = local_entity["attributes"].get("outputs"),
            **local_entity
        )
        return ae

    def merge(self, other):
        """
        Update the calling object with the attributes and classifications of
        the passed in AtlasEntity.

        :param :class:`~pyapacheatlas.core.entity.AtlasEntity` other:
            The other AtlasEntity object that you want to merge.
        """
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
        if other.classifications:
            self.classifications = (self.classifications or []).extend(self.classifications)


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
    :type inputs: Union(list(dict), :class:`pyapacheatlas.core.entity.EntityDef`)
    :param outputs:
        The list of output entities expressed as dicts and in minimum format
        (guid, type name, qualified name) or an AtlasEntity.
    :type outputs: Union(list(dict), :class:`pyapacheatlas.core.entity.EntityDef`)
    :param Union(str,int), optional guid: The guid to reference this entity by.
    :param dict, optional relationshipAttributes: The relationship attributes
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
        """
        Retrieves the inputs attribute for the process.

        :return: The list of inputs as dicts.
        :rtype: Union(list(dict),None)
        """
        return self.attributes.get("inputs")

    @inputs.setter
    def inputs(self, value):
        """
        Set the inputs attribute for the process. If you pass in a dict list, it
        should be have keys: guid, typeName, qualifiedName. Passing in a list of
        AtlasEntity, it will automatically convert the entities to dicts. If you
        set it to None, this will result in no change to the Process inputs you
        are targeting after upload. If you set it to an empty list `[]` you will
        erase all the inputs.

        :param value: List of dicts or atlas entities to set as the inputs.
        :type value: list(Union(dict, :class:`~pyapacheatlas.core.entity.AtlasEntity`))
        """
        # TODO: Consider checking if there is a valid guid to return a simpler min
        if value is not None:
            self.attributes["inputs"] = self._parse_atlas_entity(value)
        else:
            self.attributes["inputs"] = None

    @property
    def outputs(self):
        """
        Retrieves the outputs attribute for the process.

        :return: The list of outputs as dicts.
        :rtype: Union(list(dict),None)
        """
        return self.attributes.get("outputs")

    @outputs.setter
    def outputs(self, value):
        """
        Set the outputs attribute for the process. If you pass in a dict list, it
        should be have keys: guid, typeName, qualifiedName. Passing in a list of
        AtlasEntity, it will automatically convert the entities to dicts. If you
        set it to None, this will result in no change to the Process outputs you
        are targeting after upload. If you set it to an empty list `[]` you will
        erase all the outputs.

        :param value: List of dicts or atlas entities to set as the outputs.
        :type value: list(Union(dict, :class:`~pyapacheatlas.core.entity.AtlasEntity`))
        """
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
        :type args: Union(dict, :class:`pyapacheatlas.core.entity.AtlasEntity`)
        """
        self.inputs = self.inputs + self._parse_atlas_entity(args)

    def addOutput(self, *args):
        """
        Add one or many entities to the outputs.

        :param args:
            The atlas entities you are adding. They are comma delimited dicts
            or AtlasEntity. You can expand a list with `*my_list`.
        :type args: Union(dict, :class:`pyapacheatlas.core.entity.AtlasEntity`)
        """
        self.outputs = self.outputs + self._parse_atlas_entity(args)

    def merge(self, other):
        """
        Combine the inputs and outputs of a process. Fails if one side has a
        null input or output. Updates the object that merge is called on.

        :param :class:`~pyapacheatlas.core.entity.AtlasEntity` other:
            The other AtlasEntity object that you want to merge.
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


class AtlasClassification():
    """
    A python implementation of the AtlasClassification from Apache Atlas.

    :param str typeName: The name of this classification.
    :param str entityStatus: One of ACTIVE, DELETED, PURGED.
    :param bool propagate:
        Whether the classification should propagate to child entities. Not
        implemented in Purview as of release time.
    :param bool removePropagationsOnEntityDelete:
        Whether the classification should be removed on child entities if the
        parent entity is deleted. Not implemented in Purview as of release time.
    :param dict, optional attributes: Additional attributes that your
        atlas entity may require.
    :param dict, optional validityPeriods: Validity Periods that may
        be applied to this atlas classification.
    """

    def __init__(self, typeName, entityStatus="ACTIVE", propagate=False,
                 removePropagationsOnEntityDelete=False, **kwargs):
        super().__init__()
        if entityStatus not in ["ACTIVE", "PURGED", "DELETED"]:
            raise ValueError(
                f"entityStatus must be one of ACTIVE, PURGED, or DELETED.")
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
            "typeName": self.typeName,
            "entityStatus": self.entityStatus,
            "propagate": self.propagate,
            "removePropagationsOnEntityDelete": self.removePropagationsOnEntityDelete,
            "validityPeriods": self.validityPeriods,
            "attributes": self.attributes
        }
        return output
