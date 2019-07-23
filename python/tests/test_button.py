from pytest import raises

from bridge import Button
from bridge.interchange import Interaction

def test_construction():
    Button("Press me")

    with raises(TypeError):
        Button(0)

def test_callback_is_settable():
    xs = []
    b = Button('', callback=(lambda: xs.append(1)))
    b.handle_interaction(Interaction(target=b.id, type='click'))
    assert xs == [1]

    xs = []
    b.callback = (lambda: xs.append(2))
    b.handle_interaction(Interaction(target=b.id, type='click'))
    assert xs == [2]

    xs = []
    b.callback = None
    b.handle_interaction(Interaction(target=b.id, type='click'))
    assert xs == []

def test_set_callback():
    xs = []
    b = Button('')
    @b.set_callback
    def _():
        xs.append(1)

    b.handle_interaction(Interaction(target=b.id, type='click'))
    assert xs == [1]
