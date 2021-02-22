from pyapacheatlas.core.entity import AtlasClassification
from pyapacheatlas.core.typedef import (
    AtlasRelationshipEndDef, Cardinality,
    ParentEndDef, ChildEndDef
)
import sys
sys.path.append('.')


def test_json_contract_atlas_classification():
    typeName = "test"
    entityStatus = "ACTIVE"
    propagate = False
    removePropagationsOnEntityDelete = False
    validityPeriods = []
    attributes = {}

    ac = AtlasClassification(
        typeName=typeName,
        entityStatus=entityStatus,
        propagate=propagate,
        removePropagationsOnEntityDelete=removePropagationsOnEntityDelete
    )

    expected = {
        "typeName": typeName,
        "entityStatus": entityStatus,
        "propagate": propagate,
        "removePropagationsOnEntityDelete": removePropagationsOnEntityDelete,
        "validityPeriods": validityPeriods,
        "attributes": attributes
    }

    assert(ac.to_json() == expected)


def test_json_contract_atlas_relationship_enddef():
    name = "name"
    typeName = "test"
    desc = "Blah"

    are = AtlasRelationshipEndDef(
        name=name,
        typeName=typeName,
        cardinality=Cardinality.SINGLE,
        isContainer=False,
        description=desc
    )

    expected = {
        "type": typeName,
        "name": name,
        "cardinality": "SINGLE",
        "isContainer": False,
        "description": desc,
        "isLegacyAttribute": False
    }

    assert(are.to_json() == expected)

def test_json_contract_parent_enddef():
    name = "dad"
    typeName = "test"
    desc = "Blah"

    dad = ParentEndDef(
        name=name,
        typeName=typeName,
        description=desc
    )

    expected = {
        "type": typeName,
        "name": name,
        "cardinality": "SET",
        "isContainer": True,
        "description": desc,
        "isLegacyAttribute": False
    }

    assert(dad.to_json() == expected)

def test_json_contract_child6_enddef():
    name = "dad"
    typeName = "test"
    desc = "Blah"

    kid = ChildEndDef(
        name=name,
        typeName=typeName,
        description=desc
    )

    expected = {
        "type": typeName,
        "name": name,
        "cardinality": "SINGLE",
        "isContainer": False,
        "description": desc,
        "isLegacyAttribute": False
    }

    assert(kid.to_json() == expected)