from enum import Enum


class TypeCategory(Enum):
    """
    An implementation of an Atlas TypeCategory used in relationshipDefs.
    """
    CLASSIFICATION = "classification"
    ENTITY = "entity"
    ENUM = "enum"
    RELATIONSHIP = "relationship"
    STRUCT = "struct"
    BUSINESSMETADATA = "business_Metadata"
    # BusinessMetadata is used in BaseTypeDef where it is forced UPPER
    # BusinessMetadata is used in AtlasClient.upload_typedefs
    # as part of the url (converted to businessMetadata)
    # as part of the payload (converted to businessMetadataDefs)


class Cardinality(Enum):
    """
    An implementation of an Atlas Cardinality used in relationshipDefs.
    """
    SINGLE = "SINGLE"
    LIST = "LIST"
    SET = "SET"


class AtlasAttributeDef():
    """
    An implementation of AtlasAttributeDef.

    :param str name:
        The name of the Attribute Definition. Provides a standard way to pass
        in an attribute definition when defining an Entity.

    Kwargs:
        :param cardinality:
            One of Cardinality.SINGLE, .SET, .LIST. Defaults to SINGLE.
        :type cardinality: :class:`pyapacheatlas.core.typedef.Cardinality`
        :param str typeName: The type of this attribute. Defaults to string.
    """

    propertiesEnum = [
        "cardinality", "constraints", "defaultValue", "description",
        "displayName", "includeInNotification", "indexType", "isIndexable",
        "isOptional", "isUnique", "name", "options", "searchWeight",
        "typeName", "valuesMaxCount", "valuesMinCount"
    ]

    def __init__(self, name, **kwargs):
        """
        Default arguments are chosen assuming you want a single attribute
        """
        super().__init__()
         # Cardinality
        if "cardinality" in kwargs:
            if isinstance(kwargs["cardinality"], Cardinality):
                self.cardinality = kwargs.get("cardinality").value
            elif isinstance(kwargs["cardinality"], str):
                self.cardinality = kwargs.get("cardinality")
        else:
            self.cardinality = Cardinality.SINGLE.value
        # array of AtlasConstraintDef
        self.constraints = kwargs.get("constraints")
        self.defaultValue = kwargs.get("defaultValue")  # string
        self.description = kwargs.get("description")  # string
        self.displayName = kwargs.get("displayName")  # string
        self.includeInNotification = kwargs.get(
            "includeInNotification", False)  # boolean
        self.indexType = kwargs.get("indexType")  # IndexType
        self.isIndexable = kwargs.get("isIndexable", False)  # boolean
        self.isOptional = kwargs.get("isOptional", True)  # boolean
        self.isUnique = kwargs.get("isUnique", False)  # boolean
        self.name = name  # string
        self.options = kwargs.get("options")  # map of string
        self.searchWeight = kwargs.get("searchWeight")  # number
        self.typeName = kwargs.get("typeName", "string")  # string
        self.valuesMaxCount = kwargs.get("valuesMaxCount", 1)  # number
        self.valuesMinCount = kwargs.get("valuesMinCount", 0)  # number

    def to_json(self, omit_nulls=True):
        output = self.__dict__
        if omit_nulls:
            output = {k: v for k, v in output.items(
            ) if v is not None and omit_nulls}
        return output


class AtlasRelationshipAttributeDef(AtlasAttributeDef):
    """
    An implementation of AtlasRelationshipAttributeDef. Provides a standard
    way to pass in a relationship definition when defining an Entity rather
    than creating a separate relationship def.

    :param str name: The name of the Relationship Attribute Definition.
    :param str relationshipTypeName:
        The name of the relationship type being defined. Commonly uses
        'endDef1_endDef2' where endDef's are the names given based on
        the relationship being used.

    Kwargs:
        :param cardinality:
            One of Cardinality.SINGLE, .SET, .LIST. Defaults to SINGLE.
        :type cardinality: :class:`pyapacheatlas.core.typedef.Cardinality`
        :param str typeName: The type of this attribute. Defaults to string.
    """

    def __init__(self, name, relationshipTypeName, **kwargs):
        super().__init__(name, **kwargs)
        self.relationshipTypeName = relationshipTypeName


class BaseTypeDef():
    """
    An implementation of AtlasBaseTypeDef.

    :param str name: The name of the typedef.
    :param category: The category of the typedef.
    :type category: :class:`~pyapacheatlas.core.typedef.TypeCategory`
    """

    def __init__(self, name, category, **kwargs):
        super().__init__()
        self.category = category.value.upper()
        self.createTime = kwargs.get("createTime")
        self.createdBy = kwargs.get("createdBy")
        self.dateFormatter = kwargs.get("dateFormatter")
        self.description = kwargs.get("description")
        self.guid = kwargs.get("guid")
        self.name = name
        self.options = kwargs.get("options")
        self.serviceType = kwargs.get("serviceType")
        self.typeVersion = kwargs.get("typeVersion")
        self.updateTime = kwargs.get("updateTime")
        self.updatedBy = kwargs.get("updatedBy")
        self.version = kwargs.get("version")

    def to_json(self, omit_nulls=True):
        """
        Converts the typedef object to a dict / json.

        :param bool omit_null: If True, omits keys with value of None.
        :return: The dict / json version of the type def.
        :rtype: dict
        """
        output = self.__dict__
        if omit_nulls:
            output = {k: v for k, v in output.items(
            ) if v is not None and omit_nulls}
        return output


class AtlasStructDef(BaseTypeDef):
    """
    An implemention of AtlasStructDef. Not expected to be used by the end users.

    :param str name: The name of the type definition.
    :param category: The category of the typedef.
    :type category: :class:`~pyapacheatlas.core.typedef.TypeCategory`

    Kwargs:
        :param attributeDefs:
            The AtlasAttributeDefs that should be available on the struct.
        :type attributeDefs: list(Union(dict, :class:`pyapacheatlas.core.typedef.AtlasAttributeDef`))
    """

    def __init__(self, name, category, **kwargs):
        super().__init__(name=name, category=category, **kwargs)
        self.attributeDefs = kwargs.get("attributeDefs", [])

    @property
    def attributeDefs(self):
        """
        :return: List of attribute definitions.
        :rtype: list(dict)
        """
        return self._attributeDefs

    @attributeDefs.setter
    def attributeDefs(self, value):
        """
        :param value:
            The attribute defs you are adding. They are comma delimited dicts
            or AtlasAttributeDefs.
        :type value: list(Union(dict, :class:`pyapacheatlas.core.typedef.AtlasAttributeDef`))
        """
        self._attributeDefs = [
            e.to_json()
            if isinstance(e, AtlasAttributeDef)
            else e
            for e in value
        ]

    def addAttributeDef(self, *args):
        """
        Add one or many attribute definitions.

        :param args:
            The attribute defs you are adding. They are comma delimited dicts
            or AtlasAttributeDefs. You can expand a list with `*my_list`.
        :type args: Union(dict, :class:`pyapacheatlas.core.typedef.AtlasAttributeDef`)
        """
        self.attributeDefs = self.attributeDefs + [
            e.to_json()
            if isinstance(e, AtlasAttributeDef)
            else e
            for e in args
        ]

    def to_json(self, omit_nulls=True):
        """
        Convert the defintion to a JSON dict.

        :return: The definition as a dict.
        :rtype: dict
        """
        output = super().to_json(omit_nulls)
        output.update({"attributeDefs": self.attributeDefs})
        output.pop("_attributeDefs")
        return output


class ClassificationTypeDef(AtlasStructDef):
    """
    An implementation of AtlasClassificationDef

    :param str name: The name of the type definition.
    :param list(str) entityTypes: The list of entityTypes for the classification.
    :param list(str) superTypes: The list of superTypes for the classification.

    Kwargs:
        :param attributeDefs:
            The AtlasAttributeDefs that should be available on the Classification.
        :type attributeDefs: list(Union(dict, :class:`pyapacheatlas.core.typedef.AtlasAttributeDef`))
        :param list(str) subTypes: The types that will inherit this classification.
    """

    def __init__(self, name, entityTypes=[], superTypes=[], **kwargs):
        super().__init__(name, category=TypeCategory.CLASSIFICATION, **kwargs)
        self.entityTypes = entityTypes
        self.superTypes = superTypes
        self.subTypes = kwargs.get("subTypes", []) or []

    def __str__(self):
        return "<CLASSIFICATION: " + self.name + ">"


class EntityTypeDef(AtlasStructDef):
    """
    An implementation of AtlasEntityDef

    :param str name: The name of the type definition.
    :param list(str) superTypes:
        The list of superTypes for the classification. You most likely want
        ['DataSet'] to create a DataSet asset which is the default.

    Kwargs:
        :param attributeDefs:
            The AtlasAttributeDefs that should be available on the Entity.
        :type attributeDefs: list(Union(dict, :class:`pyapacheatlas.core.typedef.AtlasAttributeDef`))
    """

    def __init__(self, name, superTypes=['DataSet'], **kwargs):
        super().__init__(name, category=TypeCategory.ENTITY, **kwargs)
        self.relationshipAttributeDefs = kwargs.get(
            "relationshipAttributeDefs", []) or []
        self.superTypes = superTypes

    def __str__(self):
        return self.name

    @property
    def relationshipAttributeDefs(self):
        """
        :return: List of relationship attribute definitions.
        :rtype: list(dict)
        """
        return self._relationshipAttributeDefs

    @relationshipAttributeDefs.setter
    def relationshipAttributeDefs(self, value):
        """
        :param value:
            The attribute defs you are adding. They are comma delimited dicts
            or AtlasRelationshipAttributeDefs.
        :type value: list(Union(dict, :class:`pyapacheatlas.core.typedef.AtlasRelationshipAttributeDef`))
        """
        self._relationshipAttributeDefs = [
            e.to_json()
            if isinstance(e, AtlasRelationshipAttributeDef)
            else e
            for e in value
        ]

    def addRelationshipAttributeDef(self, *args):
        """
        Add one or many attribute definitions.

        :param args:
            The attribute defs you are adding. They are comma delimited dicts
            or AtlasAttributeDefs. You can expand a list with `*my_list`.
        :type args: Union(dict, :class:`pyapacheatlas.core.typedef.relationshipAttributeDefs`)
        """
        self.relationshipAttributeDefs = self.relationshipAttributeDefs + [
            e.to_json()
            if isinstance(e, AtlasRelationshipAttributeDef)
            else e
            for e in args
        ]

    def to_json(self, omit_nulls=True):
        """
        Convert the defintion to a JSON dict.

        :return: The definition as a dict.
        :rtype: dict
        """
        output = super().to_json(omit_nulls)
        output.update(
            {"relationshipAttributeDefs": self.relationshipAttributeDefs})
        output.pop("_relationshipAttributeDefs")
        return output


class RelationshipTypeDef(BaseTypeDef):
    """
    An implementation of AtlasRelationshipDef.

    :param str name: The name of the relationship type def.
    :param endDef1:
        Either a valid AtlasRelationshipEndDef dict or class object.
    :type endDef1:
        Union(:class:`~pyapacheatlas.core.typedef.AtlasRelationshipEndDef`, dict)
    :param endDef2:
        Either a valid AtlasRelationshipEndDef dict or class object.
    :type endDef2:
        Union(:class:`~pyapacheatlas.core.typedef.AtlasRelationshipEndDef`, dict)
    :param str relationshipCategory:
        One of COMPOSITION, AGGREGATION, ASSOCIATION. You're most likely
        looking at COMPOSITION to create a parent/child relationship.
    """

    def __init__(self, name, endDef1, endDef2, relationshipCategory, **kwargs):
        super().__init__(name, category=TypeCategory.RELATIONSHIP, **kwargs)

        self.endDef1 = endDef1
        self.endDef2 = endDef2
        self.relationshipCategory = relationshipCategory

    @property
    def endDef1(self):
        """
        :return: The first end definition.
        :rtype: dict
        """
        return self._endDef1

    @endDef1.setter
    def endDef1(self, value):
        """
        :param value:
            The first end def for you are adding. They are comma delimited dicts
            or AtlasRelationshipEndDef.
        :type value: list(Union(dict, :class:`pyapacheatlas.core.typedef.AtlasRelationshipEndDef`))
        """
        if isinstance(value, AtlasRelationshipEndDef):
            self._endDef1 = value.to_json()
        elif isinstance(value, dict):
            self._endDef1 = value
        else:
            raise NotImplementedError(
                f"An EndDef of type `{type(value)}` is not supported.")

    @property
    def endDef2(self):
        """
        :return: The second end definition.
        :rtype: dict
        """
        return self._endDef2

    @endDef2.setter
    def endDef2(self, value):
        """
        :param value:
            The second end def for you are adding. They are comma delimited
            dicts or AtlasRelationshipEndDef.
        :type value: list(Union(dict, :class:`pyapacheatlas.core.typedef.AtlasRelationshipEndDef`))
        """
        if isinstance(value, AtlasRelationshipEndDef):
            self._endDef2 = value.to_json()
        elif isinstance(value, dict):
            self._endDef2 = value
        else:
            raise NotImplementedError(
                f"An EndDef of type `{type(value)}` is not supported.")

    def to_json(self, omit_nulls=True):
        """
        Convert the defintion to a JSON dict.

        :return: The definition as a dict.
        :rtype: dict
        """
        output = super().to_json(omit_nulls)
        output.update({"endDef1": self.endDef1, "endDef2": self.endDef2})
        output.pop("_endDef1")
        output.pop("_endDef2")
        return output


class AtlasRelationshipEndDef():
    """
    An implementation of AtlasRelationshipEndDef.

    :param str name: The name that will appear on the entity's relationship attribute.
    :param str typeName: The type that is required for this end of the relationship.
    :param cardinality: The cardinality of the end definition.
    :type cardinality": :class:`~pyapacheatlas.core.typedef.Cardinality`
    :param bool isContainer:
        This should be False when the cardinality is SINGLE. It should be
        True when cardinality is SET or LIST. endDef1 should

    Kwargs:
        :param str description:
            The description of this end of the relationship.
        :param bool isLegacyAttribute: Defaults to False.
    """

    def __init__(self, name, typeName, cardinality=Cardinality.SINGLE, isContainer=False, **kwargs):
        self.cardinality = cardinality.value
        self.description = kwargs.get("description")
        self.isLegacyAttribute = kwargs.get("isLegacyAttribute", False)
        self.name = name
        self.type = typeName
        self.isContainer = isContainer

    def to_json(self, omit_nulls=True):
        """
        Converts the typedef object to a dict / json.

        :param bool omit_null: If True, omits keys with value of None.
        :return: The dict / json version of the type def.
        :rtype: dict
        """
        output = self.__dict__
        if omit_nulls:
            output = {k: v for k, v in output.items(
            ) if v is not None and omit_nulls}
        return output


class ParentEndDef(AtlasRelationshipEndDef):
    """
    A helper for creating a Parent end def (e.g. EndDef1 that is a container).
    The goal being to simplify and reduce the margin of error when creating
    containing relationships. This should be used in EndDef1 when the 
    relationshipCategory is COMPOSITION or AGGREGATION.

    Defaults to cardinality of SET and isContainer=True.
    """

    def __init__(self, name, typeName, **kwargs):
        super().__init__(
            name, typeName,
            cardinality=Cardinality.SET,
            isContainer=True, **kwargs
        )


class ChildEndDef(AtlasRelationshipEndDef):
    """
    A helper for creating a Child end def (e.g. EndDef2 that is a single).
    The goal being to simplify and reduce the margin of error when creating
    containing relationships. This should be used in EndDef2 when the 
    relationshipCategory is COMPOSITION or AGGREGATION.

    Defaults to cardinality of SINGLE and isContainer=False.
    """

    def __init__(self, name, typeName, **kwargs):
        super().__init__(
            name, typeName,
            cardinality=Cardinality.SINGLE,
            isContainer=False, **kwargs
        )
