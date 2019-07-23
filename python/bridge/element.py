from __future__ import annotations

from abc import ABC, abstractmethod, abstractproperty
from typing import Callable, Iterator, Optional, Sequence, TypeVar, TYPE_CHECKING

from . import interchange

if TYPE_CHECKING:
    from .gui import AbstractGUI

F = TypeVar('F', bound=Callable)

def _count():
    i = 0
    while True:
        yield i
        i += 1


class Element(ABC):
    _nonces = _count()
    def __init__(self, parent: Optional[Element] = None) -> None:
        super().__init__()
        self.id = str("_element_" + str(next(self._nonces)))
        self._parent = parent
        self._gui: Optional[AbstractGUI] = None

    @property
    def parent(self) -> Optional[Element]:
        '''...

        - ``x.parent == y`` must be equivalent to ``x in y.children``.
        - Consequently, you probably never want to set an Element's parent, unless you're writing your own Element class and implementing a method that adds a child. For example, ``my_list_element.append(e)`` will set ``e.parent``; end users should never have to worry about it.
        '''
        return self._parent
    @parent.setter
    def parent(self, parent: Element) -> None:
        if (self._parent is not None) and (parent is not None):
            raise RuntimeError('cannot set parent of Element that already has a parent')
        self._parent = parent

    @property
    def children(self) -> Sequence[Element]:
        '''...

        ``x.parent == y`` must be equivalent to ``x in y.children``.
        '''
        return ()

    def walk(self) -> Iterator[Element]:
        yield self
        for child in self.children:
            yield from child.walk()

    @property
    def gui(self) -> Optional[AbstractGUI]:
        if self.parent is not None:
            return self.parent.gui
        if self._gui is not None:
            return self._gui
        return None
    @gui.setter
    def gui(self, gui: AbstractGUI) -> None:
        if self.parent is not None:
            raise RuntimeError('cannot set GUI of an Element that has a parent')
        self._gui = gui

    def mark_dirty(self) -> None:
        '''Notify the GUI that owns this element (if there is one) that it needs re-rendering.'''
        if self.gui is not None:
            self.gui.mark_dirty(self)

    def handle_interaction(self, Interaction) -> None:
        pass

    @abstractmethod
    def subtree_json(self):
        pass

class List(Element):
    def __init__(self, children: Sequence[Element], **kwargs) -> None:
        super().__init__(**kwargs)
        self._children = children
        for child in self._children:
            child.parent = self

    @property
    def children(self) -> Sequence[Element]:
        return self._children

    def subtree_json(self):
        return interchange.node_json(
            'ul',
            {},
            [interchange.node_json('li', {}, [child])
             for child in self._children],
        )

class Container(Element):
    def __init__(self, children: Optional[Sequence[Element]], **kwargs) -> None:
        super().__init__(**kwargs)
        self._children = list(children) if (children is not None) else []
        for child in self._children:
            child.parent = self
    @property
    def children(self) -> Sequence[Element]:
        return self._children
    def subtree_json(self):
        return interchange.node_json('div', {}, self.children)

class Text(Element):
    def __init__(self, text: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._text = text
    @property
    def text(self) -> str:
        return self._text
    @text.setter
    def text(self, text: str) -> None:
        self._text = text
        self.mark_dirty()
    def subtree_json(self):
        return interchange.text_json(self.text)

class Button(Element):
    def __init__(self, text: str, callback: Optional[Callable[[], None]] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._text = text
        self._callback = callback
    def subtree_json(self):
        return interchange.node_json('button', {}, [interchange.text_json(self._text)])
    def handle_interaction(self, interaction):
        if interaction.type == 'click':
            if self._callback is not None:
                self._callback()

    def set_callback(self, f: F) -> F:
        '''Set the Button's ``callback``. Returns the same function, for use as a decorator.
            >>> button = Button("click")
            >>> @button.set_callback
            ... def callback():
            ...   print("Button was clicked!")
        '''
        self._callback = f
        return f

class TextField(Element):
    def __init__(self, callback: Callable[[str], None], **kwargs) -> None:
        super().__init__(**kwargs)
        self._value = ''
        self._callback = callback
    def subtree_json(self):
        return interchange.node_json('input', {'value': self._value}, [])
    def handle_interaction(self, interaction):
        if interaction.type == 'input':
            self._value = interaction.value
            self._callback(interaction.value)

    @property
    def value(self) -> str:
        return self._value
    @value.setter
    def value(self, value: str) -> None:
        self._value = value
        self.mark_dirty()
