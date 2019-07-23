from pytest import raises

from bridge import Link, Text

from . import assert_marks_dirty

def test_construction():
    text = Text('blah')
    assert text.text == 'blah'

    with raises(TypeError):
        Text(0)

def test_set_text():
    t = Text('foo')
    with assert_marks_dirty(t):
        t.text = 'bar'
    assert t.text == 'bar'

def test_link_set_url():
    link = Link(text='foo', url='http://example.com')
    with assert_marks_dirty(link):
        link.url = 'https://example.com'
    assert link.url == 'https://example.com'
