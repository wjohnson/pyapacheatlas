from pyapacheatlas.core.entity import AtlasEntity, AtlasUnInit
from pyapacheatlas.core import AtlasClassification


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

def test_explicit_add_nulls():
    ae = AtlasEntity(name="a", typeName="b", qualified_name="c", guid=-1, meanings=None, customAttributes=None)
    assert(ae.meanings is None)
    assert(ae.customAttributes is None)
    assert(ae.relationshipAttributes is not None)

def test_add_classifications():
    ae = AtlasEntity(name="a", typeName="b", qualified_name="c", guid=-1)
    ae.addClassification("a","b", AtlasClassification("c"))
    assert(ae.classifications)

    expected = [AtlasClassification("a").to_json(), AtlasClassification("b").to_json(),
    AtlasClassification("c").to_json()
    ]
    
    assert(ae.classifications == expected)

def test_add_classifications_transaction():
    ae = AtlasEntity(name="a", typeName="b", qualified_name="c", guid=-1)
    # Confirm that it will keep the initial state as uninitialized
    try:
        ae.addClassification("a","b", 123, AtlasClassification("c"))
    except Exception as e:
        pass
    assert(isinstance(ae.classifications, AtlasUnInit))
    
    # Now confirm that it will keep the initial state
    ae.addClassification("a")
    try:
        ae.addClassification(123)
    except:
        pass
    assert(ae.classifications == [AtlasClassification("a").to_json()])

def test_add_customAttribute():
    ae = AtlasEntity(name="a", typeName="b", qualified_name="c", guid=-1)
    ae.addCustomAttribute(custom1="blah")
    assert(ae.customAttributes)
    assert(ae.customAttributes == {"custom1":"blah"})

def test_add_businessAttribute():
    ae = AtlasEntity(name="a", typeName="b", qualified_name="c", guid=-1)
    ae.addBusinessAttribute(biz1={"prop1":"abc"})
    assert(ae.businessAttributes)
    assert(ae.businessAttributes == {"biz1":{"prop1":"abc"}})
