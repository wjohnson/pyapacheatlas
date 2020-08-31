import warnings
import pytest

from pyapacheatlas.core.typedef import AtlasAttributeDef
from pyapacheatlas.readers.core.entitydef import to_entityDefs

def test_entityDefs():
    # All attribute keys should be converted to camel case except "Entity TypeName"
    inputData = [
        {"Entity TypeName":"generic", "name":"attrib1", "description":"desc1",
        "isOptional":"True", "isUnique":"False", "defaultValue":None},
        {"Entity TypeName":"generic", "name":"attrib2", "description":"desc2",
        "isOptional":"True", "isUnique":"False", "defaultValue":None, 
        "cardinality":"SINGLE"},
        {"Entity TypeName":"demo", "name":"attrib3", "description":"desc3",
        "isOptional":"False", "isUnique":"False","cardinality":"SET"}
    ]

    output = to_entityDefs(inputData)
    # It is an AtlasTypesDef composite wrapper
    assert("entityDefs" in output.keys())
    # There are two entity typenames specified so there should be only two entityDefs
    assert (len(output["entityDefs"]) == 2)

    genericEntityDef = None
    demoEntityDef = None

    for entityDef in output["entityDefs"]:
        if entityDef["name"] == "generic":
            genericEntityDef = entityDef
        elif entityDef["name"] == "demo":
            demoEntityDef = entityDef
    
    # Generic has two attributes
    assert(len(genericEntityDef["attributeDefs"]) == 2)

    # Demo has one attribute
    assert(len(demoEntityDef["attributeDefs"]) == 1)

    assert(
        demoEntityDef["attributeDefs"][0] == AtlasAttributeDef(
            name="attrib3", **{"description":"desc3","isOptional":"False", 
            "isUnique":"False","cardinality":"SET"}
            ).to_json()
    )
        

    
def test_entityDefs_warns_with_extra_params():
    # All attribute keys should be converted to camel case except "Entity TypeName"
    inputData = [
        {"Entity TypeName":"generic", "name":"attrib1", "description":"desc1",
        "isOptional":"True", "isUnique":"False", "defaultValue":None},
        {"Entity TypeName":"generic", "name":"attrib2", "description":"desc2",
        "isOptional":"True", "isUnique":"False", "defaultValue":None, 
        "cardinality":"SINGLE","randomAttrib":"foobar"}
    ]

    # Assert that a UserWarning occurs when adding an extra attribute
    pytest.warns(UserWarning, to_entityDefs, **{"json_rows":inputData})
    