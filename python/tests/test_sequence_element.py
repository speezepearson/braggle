import contextlib
from unittest.mock import patch

from pytest import raises  # type: ignore

from bridge import Element, List, Text


def test_init_sets_parents():
    child = Text("hi")
    parent = List([child])
    assert list(parent.children) == [child]
    assert child.parent == parent


def test_getitem():
    children = [Text("a"), Text("b"), Text("c")]
    parent = List(children)
    assert parent[0] == children[0]
    assert list(parent[:2]) == children[:2]
    assert list(parent[:-1]) == children[:-1]
    assert list(parent[-1:]) == children[-1:]
    assert list(parent[::2]) == children[::2]
    assert list(parent[:]) == children
    assert list(parent[10:]) == children[10:]


def test_getitem__out_of_range():
    with raises(IndexError):
        List()[10]


def test_setitem():
    old = Text("old")
    new = Text("new")
    parent = List([old])
    parent[0] = new
    assert list(parent.children) == [new]
    assert old.parent is None
    assert new.parent is parent


def test_setitem__out_of_range():
    with raises(IndexError):
        List()[10] = Text


def test_setitem_slice():
    cont1 = Text("cont1")
    old1 = Text("old1")
    old2 = Text("old2")
    cont2 = Text("cont2")
    new = Text("new")
    parent = List([cont1, old1, old2, cont2])
    parent[1:3] = [new]
    assert list(parent.children) == [cont1, new, cont2]
    assert old1.parent is old2.parent is None
    assert new.parent is parent
    assert cont1.parent is cont2.parent is parent


def test_delitem():
    old = Text("old")
    cont = Text("cont")
    parent = List([old, cont])
    del parent[0]
    assert list(parent.children) == [cont]
    assert old.parent is None
    assert cont.parent is parent


def test_delitem_slice():
    cont1 = Text("cont1")
    old1 = Text("old1")
    old2 = Text("old2")
    cont2 = Text("cont2")
    new = Text("new")
    parent = List([cont1, old1, old2, cont2])
    del parent[1:3]
    assert list(parent.children) == [cont1, cont2]
    assert old1.parent is old2.parent is None
    assert cont1.parent is cont2.parent is parent
