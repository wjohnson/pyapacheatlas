from pyapacheatlas.core.entity import AtlasEntity

def test_getters_setters():
    ae = AtlasEntity(name="a", typeName="b", qualified_name="c",guid=-1)

    assert(ae.attributes["name"] == "a")
    assert(ae.attributes["qualifiedName"] == "c")

    assert(ae.name == "a")
    assert(ae.qualifiedName == "c")

    ae.name = "x"
    ae.qualifiedName = "y"

    assert(ae.attributes["name"] == "x")
    assert(ae.attributes["qualifiedName"] == "y")

