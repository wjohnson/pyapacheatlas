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
        # TODO: Figure out if there is a need for supporting another
        # type that may add extra attributes?
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

    def __init__(self, name, **kwargs):
        """
        :param str name: The name of the typedef.
        """
        super().__init__()
        self.category = kwargs.get("category").value.upper()
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


class EntityTypeDef(BaseTypeDef):
    """
    An implementation of AtlasEntityDef
    """

    def __init__(self, name, **kwargs):
        """
        :param str name: The name of the typedef.
        """
        kwargs["category"] = TypeCategory.ENTITY
        super().__init__(name, **kwargs)
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

    @staticmethod
    def default_columns_endDef(typeName):
        """
        Returns a default columns end definition. It's meant to be
        used on the table (endDef1) of table-column relationship.

        :return: An end def named columns as a SET/container.
        :rtype: dict
        """
        return {
            "type": typeName,
            "name": "columns",
            "isContainer": True,
            "cardinality": "SET",
            "isLegacyAttribute": True
        }

    @staticmethod
    def default_table_endDef(typeName):
        """
        Returns a default table end definition. It's meant to be
        used on the column (endDef2) of table-column relationship.

        :return: An end def named table as a SINGLE.
        :rtype: dict
        """
        return {
            "type": typeName,
            "name": "table",
            "isContainer": False,
            "cardinality": "SINGLE",
            "isLegacyAttribute": True
        }

    @staticmethod
    def _decide_endDef(endDef, default_func):
        """

        :param Union(str, dict) endDef: Either a string to be passed into
            the default_func or a dict.  If dict, it will be assumed that
            it's a valid end def.
        :param function default_func: The default function to use if endDef
            is not a dict.  default_func must take one str parameter.
        """
        output = None

        if isinstance(endDef, dict):
            output = endDef
        elif isinstance(endDef, str):
            output = default_func(endDef)

        else:
            raise NotImplementedError(
                "endDef1 of type {} is not supported. Use string or dict.".format(type(endDef)))
        return output

    def __init__(self, name, endDef1, endDef2, **kwargs):
        """
        :param str name: The name of the relationship type def.
        :param Union(str, dict) endDef1: Either the name to be passed into
            a default_columns_endDef function or a valid endDef dict.
        :param Union(str, dict) endDef2: Either the name to be passed into
            a default_table_endDef function or a valid endDef dict.
        """
        kwargs["category"] = TypeCategory.RELATIONSHIP
        super().__init__(name, **kwargs)

        self.endDef1 = RelationshipTypeDef._decide_endDef(
            endDef1, RelationshipTypeDef.default_columns_endDef)
        self.endDef2 = RelationshipTypeDef._decide_endDef(
            endDef2, RelationshipTypeDef.default_table_endDef)
        self.relationshipCategory = kwargs.get("relationshipCategory")
