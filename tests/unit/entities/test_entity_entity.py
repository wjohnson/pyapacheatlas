from pyapacheatlas.core.entity import AtlasEntity


def test_getters_setters():
    ae = AtlasEntity(name="a", typeName="b", qualified_name="c", guid=-1)

    assert(ae.attributes["name"] == "a")
    assert(ae.attributes["qualifiedName"] == "c")

    assert(ae.name == "a")
    assert(ae.qualifiedName == "c")

    ae.name = "x"
    ae.qualifiedName = "y"

    assert(ae.attributes["name"] == "x")
    assert(ae.attributes["qualifiedName"] == "y")


def test_set_guid():
    r = AtlasEntity(name="x", typeName="y", qualified_name="z", guid=-2)

    assert(r.guid == -2)
    assert(r.to_json(minimum=True)["guid"] == -2)


def test_add_relationshipAttributes():
    ae = AtlasEntity(name="a", typeName="b", qualified_name="c", guid=-1)
    r = AtlasEntity(name="x", typeName="y", qualified_name="z", guid=-2)
    r2 = AtlasEntity(name="x2", typeName="y2", qualified_name="z2", guid=-3)
    r3 = AtlasEntity(name="x3", typeName="y3", qualified_name="z3", guid=-4)

    ae.addRelationship(test=r, test2=r2)

    # Add an update manually to make sure I'm not breaking anything
    ae.relationshipAttributes.update({"test3": r3.to_json(minimum=True)})

    assert(len(ae.relationshipAttributes) == 3)
    assert(all([isinstance(d, dict)
                for d in ae.relationshipAttributes.values()]))

    # Each should have the three minimum attributes
    req_keys = set(["guid", "qualifiedName", "typeName"])
    assert(all([(len(d) == 3 and set(d.keys()) == req_keys)
                for d in ae.relationshipAttributes.values()]))
