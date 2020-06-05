import pytest  # type: ignore
from braggle import Grid, Text
from braggle.protobuf import element_pb2
from . import assert_marks_dirty

def test_construction():
    Grid(n_rows=3, n_columns=3)

    with pytest.raises(TypeError):
        Grid(n_rows=-3, n_columns=3)

    with pytest.raises(TypeError):
        Grid(n_rows='hi', n_columns=3)
    with pytest.raises(TypeError):
        Grid(n_rows=3, n_columns='hi')

    with pytest.raises(TypeError):
        Grid([['hi']])

def test_constructor_guesses_dimensions():
    g = Grid([[Text('a')], [Text('b'), None, Text('d')]])
    assert g.n_rows == 2
    assert g.n_columns == 3

def test_getitem():
    a, b, c, d = Text('a'), Text('b'), Text('c'), Text('d')
    g = Grid([[a,b], [c,d]])

    with pytest.raises(TypeError):
        g[0]
    with pytest.raises(TypeError):
        g[0,'hi']
    with pytest.raises(IndexError):
        g[3,0]

    assert g[0,0] == a
    assert list(g[0,:]) == [a,b]
    assert list(g[:,0]) == [a,c]

def test_setitem():
    a, b, c, d = Text('a'), Text('b'), Text('c'), Text('d')
    g = Grid([[a], [c, d]])

    g[0, 1] = b
    assert b.parent == g
    assert_grid_like(g, [[a,b],[c,d]])

    t = Text('t')
    g[0,1] = t
    assert b.parent is None
    assert t.parent == g
    assert_grid_like(g, [[a,t],[c,d]])

def test_setitem__marks_dirty():
    g = Grid([[Text('before')]])
    with assert_marks_dirty(g):
        g[0,0] = Text('after')

def test_delitem():
    a, b, c, d = Text('a'), Text('b'), Text('c'), Text('d')
    g = Grid([[a], [c, d]])

    del g[1,0]
    assert c.parent is None
    assert_grid_like(g, [[a, None], [None, d]])

def test_delitem__marks_dirty():
    g = Grid([[Text('a')]])
    with assert_marks_dirty(g):
        del g[0,0]

def assert_grid_like(grid, xss):
    for r in range(grid.n_rows):
        for c in range(grid.n_columns):
            assert grid[r,c] == xss[r][c]

def test_set_n_rows():
    a, b, c, d = Text('a'), Text('b'), Text('c'), Text('d')
    g = Grid([[a, b], [c, d]])

    g.n_rows = 1
    assert a.parent == g
    assert b.parent == g
    assert c.parent is None
    assert d.parent is None
    assert_grid_like(g, [[a,b]])
    assert g.n_rows == 1
    with pytest.raises(IndexError):
        g[1,0]

    g.n_rows = 2
    assert g[1,0] is None
    assert_grid_like(g, [[a,b],[None,None]])
    g[1,0] = c
    assert c.parent == g
    assert_grid_like(g, [[a,b],[c,None]])

def test_set_n_rows_to_0():
    g = Grid(n_rows=2, n_columns=1)
    g.n_rows = 0
    g.n_rows = 1

def test_set_n_columns_to_0():
    g = Grid(n_rows=1, n_columns=2)
    g.n_columns = 0
    g.n_columns = 1


def test_set_n_columns():
    a, b, c, d = Text('a'), Text('b'), Text('c'), Text('d')
    g = Grid([[a, b], [c, d]])

    g.n_columns = 1
    assert a.parent == g
    assert c.parent == g
    assert b.parent is None
    assert d.parent is None
    assert_grid_like(g, [[a],[c]])
    assert g.n_columns == 1
    with pytest.raises(IndexError):
        g[0,1]

    g.n_columns = 2
    assert g[0,1] is None
    assert_grid_like(g, [[a,None],[c,None]])
    g[0,1] = b
    assert b.parent == g
    assert_grid_like(g, [[a,b],[c,None]])

def test_set_dimensions__marks_dirty():
    g = Grid([[Text('a')]])
    with assert_marks_dirty(g):
        g.n_rows = 2
    with assert_marks_dirty(g):
        g.n_rows = 0
    with assert_marks_dirty(g):
        g.n_rows = 1
    with assert_marks_dirty(g):
        g.n_columns = 2
    with assert_marks_dirty(g):
        g.n_columns = 0
    with assert_marks_dirty(g):
        g.n_columns = 1

def test_protobuf():
    a, b, c = Text('a'), Text('b'), Text('c')
    pb = Grid([[a, b, None], [c, None, None]]).to_protobuf()
    assert pb.tag.tagname == 'table'
    assert len(pb.tag.children) == 2
    for i, row in enumerate(pb.tag.children):
        assert len(row.tag.children) == 3, i
    assert list(pb.tag.children[0].tag.children[0].tag.children) == [element_pb2.Element(ref=a.id)]
    assert list(pb.tag.children[0].tag.children[1].tag.children) == [element_pb2.Element(ref=b.id)]
    assert list(pb.tag.children[0].tag.children[2].tag.children) == []

def test_misc():
    g = Grid([[None]])
    g[0,0] = None
    del g[0,0]
    assert g[0,0] is None
