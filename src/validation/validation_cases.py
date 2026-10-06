"""Hand-auditable cases. All time fields are exact rationals, not floats."""
from copy import deepcopy
from .model import normalize


def c(cid, u, v, start, end, rate=4, delay=0, quota=4):
    return dict(id=cid, u=u, v=v, start=start, end=end, rate=rate, delay=delay, quota=quota)


def b(source, dest, g=0, size=4, name='bundle'):
    return dict(id=name, source=source, dest=dest, g=g, size=size)


def make(name, contacts, bundles, buffers=None, horizon=12, background=None, expected=None, delta=1):
    nodes = {x for edge in contacts for x in (edge['u'], edge['v'])}
    nodes |= {x for item in bundles for x in (item['source'], item['dest'])}
    return normalize(dict(name=name, contacts=contacts, bundles=bundles,
                          buffers=buffers or {v: 4 for v in sorted(nodes)}, horizon=horizon,
                          background=background or {}, expected=expected, delta=delta))


def walkthrough():
    return make('06_sequential_walkthrough', [
        c('c1','X','B',2,3), c('c2','B','D',6,7,delay=1),
        c('c3','A','B',1,2), c('c4','A','B',7,9,quota=8),
        c('c5','B','D',10,11,delay=1), c('c6','A','C',1,2,delay=1),
        c('c7','C','D',4,5,quota=2), c('c8','C','D',2,3)],
        [b('X','D',0,name='bundle1'), b('A','D',1,name='bundle2')], expected=[8,12])


def cases():
    return [
        make('01_unique', [c('a','A','B',0,1),c('b','B','D',2,3)], [b('A','D')], expected=[3]),
        make('02_multiple', [c('a','A','B',0,1),c('b','B','D',2,3),c('c','A','D',4,5)], [b('A','D')], expected=[3]),
        make('03_no_route', [c('a','A','B',0,1),c('b','B','D',2,3,quota=3)], [b('A','D')], expected=[None]),
        make('04_late_label', [c('a','A','B',1,8,quota=4),c('b','B','D',9,10)],
             [b('A','D',1)], background={'B': [[[2,3,0,4],[3,6,4,4],[6,7,4,0]]]}, expected=[10]),
        make('05_prunable', [c('a','A','B',0,3,quota=4),c('b','B','D',4,5)], [b('A','D')], expected=[5]),
        walkthrough(),
        make('07_finish_at_end_nonzero_delay', [c('a','A','D',0,1,delay=2)], [b('A','D')], expected=[3]),
        make('08_receive_overflow', [c('a','A','D',0,1)], [b('A','D')],
             background={'D': [[[0,2,1,1]]]}, expected=[None]),
        make('09_sender_drain_overflow', [c('a','A','D',0,2,rate=2)], [b('A','D')],
             background={'A': [[[0,1,0,3],[1,2,3,0]]]}, expected=[None]),
        make('10_source_equals_destination', [], [b('A','A')], expected=[0]),
        make('11_source_full', [c('a','A','D',0,1)], [b('A','D')],
             background={'A': [[[0,2,1,1]]]}, expected=[None]),
        make('12_cycle_needed', [c('a','A','B',0,1),c('b','B','A',3,4),c('c','A','D',5,6)],
             [b('A','D')], background={'A': [[[1,2,0,4],[2,3,4,0]]]}, expected=[6]),
        make('13_quota_reuse', [c('a','A','B',0,6,quota=4),c('b','B','A',2,3),c('d','B','D',6,7)],
             [b('A','D')], background={'A': [[[0,1,0,4],[1,2,4,0]]],
                                        'B': [[[3,4,0,4],[4,5,4,0]]]}, expected=[None]),
        make('14_destination_event_peak', [c('a','A','D',0,1)], [b('A','D')],
             background={'D': [[[1,1,1,1]]]}, expected=[None]),
    ]


def fractional_gap(delta=1):
    # An accepted previous bundle of size 4 transmits from B during [1,3] at rate 2.
    # All contact boundaries, durations and background breakpoints are integer.
    return make('CE_grid_vs_continuous', [c('a','A','B',0,3),c('b','B','D',2,4,quota=4)],
                [b('A','D')], buffers={'A':4,'B':5,'D':4}, horizon=4, delta=delta,
                background={'B': [[[0,1,4,4],[1,3,4,0]]]}, expected=None)
