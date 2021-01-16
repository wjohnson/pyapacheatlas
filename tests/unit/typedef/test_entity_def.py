import json

from pyapacheatlas.core.typedef import (
    AtlasRelationshipAttributeDef,
    ClassificationTypeDef,
    EntityTypeDef,
)


def test_entity_def_add_relationshipAttribs():
    e = EntityTypeDef(name="test",
                      relationshipAttributeDefs=[
                          AtlasRelationshipAttributeDef("test", "test_rel"),
                          AtlasRelationshipAttributeDef(
                              "test2", "test_rel2").to_json()
                      ]
                      )

    e.addRelationshipAttributeDef(
        AtlasRelationshipAttributeDef("test3", "test_rel3"),
        AtlasRelationshipAttributeDef("test3", "test_rel3").to_json()
    )

    assert(len(e.relationshipAttributeDefs) == 4)
    assert(all([isinstance(i, dict) for i in e.relationshipAttributeDefs]))
