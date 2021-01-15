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
        self.cardinality = kwargs.get(
            "cardinality", Cardinality.SINGLE.value)  # Cardinality
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


class BaseTypeDef():
    """
    An implementation of AtlasBaseTypeDef
    """

    def __init__(self, name, category, **kwargs):
        """
        :param str name: The name of the typedef.
        :param category: The name of the typedef.
        :type category: :class:`~pyapacheatlas.core.typedef.TypeCategory`
        """
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

class ClassificationTypeDef(BaseTypeDef):
    """
    An implementation of AtlasClassificationDef
    """
    def __init__(self, name, entityTypes = [], superTypes = [], **kwargs):
        """
        :param str name: The name of the typedef.
        """
        super().__init__(name, category=TypeCategory.CLASSIFICATION, **kwargs)
        self.entityTypes = entityTypes
        self.superTypes = superTypes
        self.subTypes = kwargs.get("subTypes", []) or []
        self.attributeDefs = kwargs.get("attributeDefs", []) or []

    def __str__(self):
        return self.name


class EntityTypeDef(BaseTypeDef):
    """
    An implementation of AtlasEntityDef
    """

    def __init__(self, name, **kwargs):
        """
        :param str name: The name of the typedef.
        """
        super().__init__(name, category=TypeCategory.ENTITY, **kwargs)
        self.attributeDefs = kwargs.get("attributeDefs", []) or []
        self.relationshipAttributeDefs = kwargs.get(
            "relationshipAttributeDefs", []) or []
        self.superTypes = kwargs.get("superTypes", []) or []
        # Process supertype inherits inputs and outputs relationshipattribute

    def __str__(self):
        return self.name


class RelationshipTypeDef(BaseTypeDef):
    """
    An implementation of AtlasRelationshipDef
    """

    def __init__(self, name, endDef1, endDef2, relationshipCategory, **kwargs):
        """
        :param str name: The name of the relationship type def.
        :param endDef1:
            Either a valid AtlasRelationshipEndDef dict or class object.
        :type endDef1:
            Union(:class:~pyapacheatlas.core.typedef.AtlasRelationshipEndDef, dict)
        :param endDef2:
            Either a valid AtlasRelationshipEndDef dict or class object.
        :type endDef2:
            Union(:class:~pyapacheatlas.core.typedef.AtlasRelationshipEndDef, dict)
        :param str relationshipCategory:
            One of COMPOSITION, AGGREGATION, ASSOCIATION. You're most likely
            looking at COMPOSITION to create a parent/child relationship.
        """
        super().__init__(name, category=TypeCategory.RELATIONSHIP, **kwargs)

        self.endDef1 = endDef1
        self.endDef2 = endDef2
        self.relationshipCategory = relationshipCategory
    
    @property
    def endDef1(self):
        return self._endDef1
    
    @endDef1.setter
    def endDef1(self, value):
        if isinstance(value, AtlasRelationshipEndDef):
            self._endDef1=value.to_json()
        elif isinstance(value, dict):
            self._endDef1 = value
        else:
            raise NotImplementedError(f"An EndDef of type `{type(value)}` is not supported.")

    @property
    def endDef2(self):
        return self._endDef2
    
    @endDef2.setter
    def endDef2(self, value):
        if isinstance(value, AtlasRelationshipEndDef):
            self._endDef2=value.to_json()
        elif isinstance(value, dict):
            self._endDef2 = value
        else:
            raise NotImplementedError(f"An EndDef of type `{type(value)}` is not supported.")
    
    def to_json(self, omit_nulls=True):
        output = super().to_json(omit_nulls)
        output.update({"endDef1":self.endDef1, "endDef2":self.endDef2})
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
    def __init__(self, name, typeName, cardinality = Cardinality.SINGLE, isContainer=False, **kwargs):
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
    """

    def __init__(self, name, typeName, **kwargs):
        super().__init__(name, typeName, 
        cardinality = Cardinality.SET, 
        isContainer=True, **kwargs
    )

class ChildEndDef(AtlasRelationshipEndDef):
    """
    A helper for creating a Child end def (e.g. EndDef2 that is a single).
    The goal being to simplify and reduce the margin of error when creating
    containing relationships. This should be used in EndDef2 when the 
    relationshipCategory is COMPOSITION or AGGREGATION.
    """
    def __init__(self, name, typeName, **kwargs):
        super().__init__(name, typeName, 
        cardinality = Cardinality.SINGLE, 
        isContainer=False, **kwargs
    )