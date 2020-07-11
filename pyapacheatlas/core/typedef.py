import json
from enum import Enum

class TypeCategory(Enum):
    CLASSIFICATION="classification"
    ENTITY="entity"
    ENUM="enum"
    RELATIONSHIP="relationship"
    STRUCT="struct"

class Cardinality(Enum):
    SINGLE="SINGLE"
    LIST="LIST"
    SET="SET"

class BaseTypeDef():

    def __init__(self, name, **kwargs):
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
    
    def to_json(self, omit_nulls = True):
        output = self.__dict__
        if omit_nulls:
            output = {k:v for k,v in output.items() if v is not None}
        return output
        

class EntityTypeDef(BaseTypeDef):

    def __init__(self, name, **kwargs):
        kwargs["category"] = TypeCategory.ENTITY
        super().__init__(name, **kwargs)
        self.attributeDefs = kwargs.get("attributeDefs", [])
        self.relationshipAttributeDefs = kwargs.get("relationshipAttributeDefs", [])
        self.superTypes = kwargs.get("superTypes", [])
        # Process supertype inherits inputs and outputs relationshipattribute
            
    def __str__(self):
        return self.name

    
class RelationshipTypeDef(BaseTypeDef):

    @staticmethod
    def default_columns_endDef(typeName):
        return {
        "type": typeName,
        "name": "columns",
        "isContainer": True,
        "cardinality": "SET",
        "isLegacyAttribute": True
        }

    @staticmethod
    def default_table_endDef(typeName):
        return {
        "type": typeName,
        "name": "table",
        "isContainer": False,
        "cardinality": "SINGLE",
        "isLegacyAttribute": True
        }

    @staticmethod
    def _decide_endDef(endDef, default_func):
        output = None
        
        if isinstance(endDef, dict):
            output = endDef
        elif isinstance(endDef, str):
            output = default_func(endDef)

        else:
            raise NotImplementedError("endDef1 of type {} is not supported. Use string or dict.".format(type(endDef)))
        return output

    def __init__(self, name, endDef1, endDef2, **kwargs):
        kwargs["category"] = TypeCategory.RELATIONSHIP
        super().__init__(name, **kwargs)

        self.endDef1 = RelationshipTypeDef._decide_endDef(endDef1, RelationshipTypeDef.default_columns_endDef)
        self.endDef2 = RelationshipTypeDef._decide_endDef(endDef2, RelationshipTypeDef.default_table_endDef)
