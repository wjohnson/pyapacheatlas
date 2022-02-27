import json

from pyapacheatlas.core.typedef import (
    AtlasAttributeDef, 
    AtlasStructDef,
    Cardinality,
    ClassificationTypeDef,
    EntityTypeDef,
    TypeCategory
)


def test_add_attributes_at_start():
    s = AtlasStructDef(name="blah", category=TypeCategory.ENTITY,
    attributeDefs = [
        AtlasAttributeDef(name="test"),
        AtlasAttributeDef(name="test2").to_json(),
        AtlasAttributeDef(name="test3")
        ]
    )
    c = ClassificationTypeDef(name="blah",
        attributeDefs = [AtlasAttributeDef(name="test"),
            AtlasAttributeDef(name="test2").to_json(),
            AtlasAttributeDef(name="test3")]
    )
    ent = EntityTypeDef(name="blah",
        attributeDefs = [AtlasAttributeDef(name="test"),
            AtlasAttributeDef(name="test2").to_json(),
            AtlasAttributeDef(name="test3")]
    )

    # Base Struct handles this
    assert(len(s.attributeDefs) == 3)
    assert( all( [isinstance(e, dict) for e in s.attributeDefs]))

    # ClassificationDefs should also handle this behavior
    assert(len(c.attributeDefs) == 3)
    assert( all( [isinstance(e, dict) for e in c.attributeDefs]))

    # EntityDefs should also handle this behavior
    assert(len(ent.attributeDefs) == 3)
    assert( all( [isinstance(e, dict) for e in ent.attributeDefs]))


def test_add_attributes_later():
    s = AtlasStructDef(name="blah", category=TypeCategory.ENTITY)

    a1 = AtlasAttributeDef(name="test")
    a2 = AtlasAttributeDef(name="test2").to_json()

    s.addAttributeDef(a1, a2)

    assert(len(s.attributeDefs) == 2)
    assert( all( [isinstance(e, dict) for e in s.attributeDefs]))

def test_attributedef_cardinality():
    str_input = AtlasAttributeDef(name="test", cardinality="BLAH")
    enum_input =AtlasAttributeDef(name="test", cardinality=Cardinality.SET)
    no_input = AtlasAttributeDef(name="test")

    assert(str_input.cardinality == "BLAH")
    assert(enum_input.cardinality == "SET")
    assert(no_input.cardinality == "SINGLE")