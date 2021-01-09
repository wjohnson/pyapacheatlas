from pyapacheatlas.core.entity import AtlasClassification
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
