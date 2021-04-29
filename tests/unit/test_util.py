import sys
sys.path.append('.')

from pyapacheatlas.core import AtlasEntity
from pyapacheatlas.core.util import batch_dependent_entities, GuidTracker

def test_batches_entities_simple():
    entities = [AtlasEntity(str(i),"DataSet", str(i), guid=i).to_json() for i in range(0,10)]
    results = batch_dependent_entities(entities, batch_size=2)

    assert(len(results) == 5)

def test_batches_entities_dependent():
    gt = GuidTracker()
    a = AtlasEntity("A", "DataSet", "A", guid=gt.get_guid())
    b = AtlasEntity("B", "DataSet", "B", guid=gt.get_guid())
    b.addRelationship(table=a)
    c = AtlasEntity("C", "DataSet", "C", guid=gt.get_guid())
    d = AtlasEntity("D", "DataSet", "D", guid=gt.get_guid())
    c.addRelationship(parent=b)
    d.addRelationship(parent=b)
    e = AtlasEntity("E", "DataSet", "E", guid=gt.get_guid())
    e.addRelationship(table=a)
    f = AtlasEntity("F", "DataSet", "F", guid=gt.get_guid())
    g = AtlasEntity("G", "DataSet", "G", guid=gt.get_guid())
    g.addRelationship(table=f)
    h = AtlasEntity("H", "DataSet", "H", guid=gt.get_guid())
    h.addRelationship(parent=g)
    # Intentionally out of order
    j = AtlasEntity("J", "DataSet", "J", guid=gt.get_guid())
    k = AtlasEntity("K", "DataSet", "K", guid=gt.get_guid())
    i = AtlasEntity("I", "DataSet", "I", guid=gt.get_guid())

    i.addRelationship(colA=j)
    i.addRelationship(colB=k)
    
    l = AtlasEntity("L", "DataSet", "L", guid=gt.get_guid())
    m = AtlasEntity("M", "DataSet", "M", guid=gt.get_guid())
    n = AtlasEntity("N", "DataSet", "N", guid=gt.get_guid())
    o = AtlasEntity("O", "DataSet", "O", guid=gt.get_guid())
    p = AtlasEntity("P", "DataSet", "P", guid=gt.get_guid())
   
    entities = [x.to_json() for x in [a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p]]
    results = batch_dependent_entities(entities, batch_size=7)
    # There are sixteen results, batch size of 7 means at least three groups
    # One group has seven connected
    # One group should have only three
    # All others are independent 
    assert(len(results) == 3)

def test_batches_entities_with_real_guid():
    gt = GuidTracker()
    a = AtlasEntity("A", "DataSet", "A", guid=gt.get_guid())
    b = AtlasEntity("B", "DataSet", "B", guid=gt.get_guid())
    b.addRelationship(table=a)
    
    c = AtlasEntity("C", "DataSet", "C", guid=gt.get_guid())
    d = AtlasEntity("D", "DataSet", "D", guid=gt.get_guid())
    c.addRelationship(tester={"guid":"abc-123"})

    entities = [x.to_json() for x in [a, b, c, d]]
    results = batch_dependent_entities(entities, batch_size=2)

    assert(len(results) == 2)