import contextlib
from unittest.mock import patch

from pytest import raises  # type: ignore

from braggle import Element, List, Text
from . import assert_marks_dirty

def test_construction():
    List()
    List(children=[List()])
    List(numbered=True)
    List(numbered=False)

def test_constructor_accepts_generator():
    assert len(List(Text("") for _ in range(10))) == 10

def test_conversion_to_list():
    children = [Text(str(i)) for i in range(10)]
    top = List(list(children))
    assert list(top) == children

def test_getitem():
    first = Text('1')
    second = Text('2')
    top = List(children=(first, second))

    assert top[0] == first
    assert top[1] == second
    with raises(IndexError):
        top[2]

def test_delitem_intindex():
    first = Text('1')
    second = Text('2')
    top = List(children=(first, second))

    del top[0]
    assert first.parent is None
    assert list(top) == [second]
    assert second == top[0]
    with raises(IndexError):
        top[1]

def test_delitem_sliceindex():
    numbers = [Text(c) for c in '1234567890']
    l = List(numbers)

    del l[2:7:2]
    assert all(t.parent is None for t in numbers[2:7:2])
    assert [t.text for t in l] == list('1246890')

def test_delitem__marks_dirty():
    l = List([Text('a')])
    with assert_marks_dirty(l):
        del l[0]

def test_setitem_intindex():
    first = Text('1')
    second = Text('2')
    new = Text('new')
    top = List(children=(first, second))

    top[0] = new
    assert top[0] == new
    assert first.parent is None
    assert top == new.parent
    assert list(top) == [new, second]

def test_setitem_sliceindex():
    numbers = [Text(c) for c in '1234567890']
    letters = [Text(c) for c in 'abc']
    l = List(numbers)
    l[2:7:2] = letters
    assert all(t.parent is None for t in numbers[2:6:2])
    assert all(t.parent is l for t in letters)
    assert [t.text for t in l] == list('12a4b6c890')

def test_setitem__marks_dirty():
    l = List([Text('a')])
    with assert_marks_dirty(l):
        l[0] = Text('b')

def test_insert():
    first = Text('1')
    second = Text('2')
    third = Text('3')
    fourth = Text('4')
    top = List()

    top.insert(0, second)
    assert top == second.parent
    assert list(top) == [second]

    top.insert(0, first)
    assert list(top) == [first, second]

    top.insert(99, fourth)
    assert list(top) == [first, second, fourth]

    top.insert(-1, third)
    assert list(top) == [first, second, third, fourth]

def test_insert__marks_dirty():
    l = List()
    with assert_marks_dirty(l):
        l.append(Text('a'))

def test_insert__marks_descendants_dirty():
    grandchild = Text('a'); print(id(grandchild))
    child = List([grandchild]); print(id(child))
    l = List(); print(id(l))
    with assert_marks_dirty(child), assert_marks_dirty(grandchild):
        l.append(child)

def test_children_must_be_elements():
    with raises(TypeError):
        List(children=[0])

def test_set_numbered__marks_dirty():
    l = List(numbered=True)
    with assert_marks_dirty(l):
        l.numbered = False
    with assert_marks_dirty(l):
        l.numbered = True

def test_to_protobuf():
    assert List([Text('a')], numbered=True).to_protobuf().tag.tagname == 'ol'

    l = List([Text('a')])
    j = l.to_protobuf().tag
    assert j.tagname == 'ul'
    assert j.children[0].tag.tagname == 'li'
    assert j.children[0].tag.children[0].ref == l[0].id
