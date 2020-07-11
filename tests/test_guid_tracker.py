import sys
sys.path.append('.')

from pyapacheatlas.core.util import GuidTracker

def test_guid_tracker_get_and_decrement():

    gt = GuidTracker(-100, "decrease")
    results = gt.get_guid()

    expected = -101

    assert(expected == results)
    
    second_expected = -102
    second_results = gt.get_guid()

    assert(second_expected == second_results)

def test_peek():
    gt = GuidTracker(-100, "decrease")
    peek_results = gt.peek_next_guid()
    results = gt.get_guid()

    expected = -101

    assert(expected == results)
    assert(results == peek_results)