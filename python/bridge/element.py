from __future__ import annotations

from abc import ABC, abstractmethod, abstractproperty
from typing import Callable, Iterable, Iterator, MutableSequence, Optional, overload, Sequence, TypeVar, TYPE_CHECKING

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
    __nonces = _count()
    def __init__(self, parent: Optional[Element] = None) -> None:
        super().__init__()
        self._id = str(next(self.__nonces))
        self._parent = parent
        self._gui: Optional[AbstractGUI] = None

    @property
    def id(self) -> str:
        return self._id

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

    def mark_dirty(self, *, recursive: bool = False) -> None:
        '''Notify the GUI that owns this element (if there is one) that it needs re-rendering.'''
        if self.gui is not None:
            self.gui.mark_dirty(self)
        if recursive:
            for child in self.children:
                child.mark_dirty(recursive=True)

    def handle_interaction(self, Interaction) -> None:
        pass

    @abstractmethod
    def subtree_json(self):
        pass

class SequenceElement(Element, MutableSequence[Element]):
    def __init__(self, children: Sequence[Element] = (), **kwargs) -> None:
        if not all(isinstance(child, Element) for child in children):
            raise TypeError("List children must be Elements")
        super().__init__(**kwargs)
        self._children: MutableSequence[Element] = []
        self[:] = children

    @property
    def children(self) -> Sequence[Element]:
        return tuple(self._children)

    @overload
    def __getitem__(self, index: int) -> Element:
        pass
    @overload
    def __getitem__(self, index: slice) -> MutableSequence[Element]:
        pass
    def __getitem__(self, index):
        return self.children[index]

    def __update_children(self, new_children: MutableSequence[Element]) -> None:
        old_children = self._children
        for added_child in set(new_children) - set(old_children):
            added_child.parent = self

        self._children = new_children

        for removed_child in set(old_children) - set(new_children):
            removed_child.parent = None

        self.mark_dirty()


    @overload
    def __setitem__(self, index: int, child: Element) -> None:
        pass
    @overload
    def __setitem__(self, index: slice, child: Iterable[Element]) -> None:
        pass
    def __setitem__(self, index, child):
        new_children = list(self._children)
        new_children[index] = child
        self.__update_children(new_children)

    @overload
    def __delitem__(self, index: int) -> None:
        pass
    @overload
    def __delitem__(self, index: slice) -> None:
        pass
    def __delitem__(self, index):
        new_children = list(self._children)
        del new_children[index]
        self.__update_children(new_children)

    def __len__(self) -> int:
        return len(self.children)

    def insert(self, index: int, child: Element) -> None:
        if not isinstance(child, Element):
            raise TypeError("List children must be Elements")
        child.parent = self
        self._children.insert(index, child)
        self.mark_dirty()

class List(SequenceElement):
    """A list of elements.

    May be numbered or bulleted, according to the `numbered` property (a boolean).

    Supports pretty much all the operations that a normal list does, e.g.

        my_list = List(items=[first, second])
        my_list.append(third)
        my_list.insert(0, new_first)
        assert my_list[0] is new_first
        my_list[1] = new_second
        del my_list[2]
    """
    def __init__(self, children: Sequence[Element] = (), numbered: bool = False, **kwargs) -> None:
        super().__init__(children=children, **kwargs)
        self._numbered = numbered

    @property
    def numbered(self) -> bool:
        return self._numbered
    @numbered.setter
    def numbered(self, value: bool) -> None:
        self._numbered = value
        self.mark_dirty()

    def subtree_json(self):
        return interchange.node_json(
            'ol' if self.numbered else 'ul',
            {},
            [interchange.node_json('li', {}, [child])
             for child in self._children],
        )

class Container(SequenceElement):
    def subtree_json(self):
        return interchange.node_json('div', {}, self.children)

class Text(Element):
    def __init__(self, text: str, **kwargs) -> None:
        super().__init__(**kwargs)
        if not isinstance(text, str):
            raise TypeError(text)
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

class Bold(Text):
    def subtree_json(self):
        return interchange.node_json(
            'b',
            {},
            [interchange.text_json(self.text)],
        )
class CodeSnippet(Text):
    def subtree_json(self):
        return interchange.node_json(
            'code',
            {'style': 'white-space:pre'},
            [interchange.text_json(self.text)],
        )
class CodeBlock(Text):
    def subtree_json(self):
        return interchange.node_json(
            'pre',
            {},
            [interchange.text_json(self.text)],
        )
class Link(Text):
    """A `hyperlink <http://github.com/speezepearson/browsergui>`_."""
    def __init__(self, *, text: str, url: str, **kwargs):
        super().__init__(text, **kwargs)
        self._url = url

    def subtree_json(self):
        return interchange.node_json(
            'a',
            {'href': self.url},
            [interchange.text_json(self.text)],
        )

    @property
    def url(self) -> str:
        '''The URL to which the link points.'''
        return self._url
    @url.setter
    def url(self, url: str) -> None:
        self._url = url
        self.mark_dirty()


class Button(Element):
    def __init__(self, text: str, callback: Optional[Callable[[], None]] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        if not isinstance(text, str):
            raise TypeError(text)
        self._text = text
        self.callback = callback
    def subtree_json(self):
        return interchange.node_json('button', {}, [interchange.text_json(self._text)])
    def handle_interaction(self, interaction):
        if interaction.type == 'click':
            if self.callback is not None:
                self.callback()

    def set_callback(self, f: F) -> F:
        '''Set the Button's ``callback``. Returns the same function, for use as a decorator.
            >>> button = Button("click")
            >>> @button.set_callback
            ... def callback():
            ...   print("Button was clicked!")
        '''
        self.callback = f
        return f

class LineBreak(Element):
    def subtree_json(self):
        return interchange.node_json('br', {}, [])

class TextField(Element):
    def __init__(self, callback: Optional[Callable[[str], None]] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._value = ''
        self._callback = callback
    def subtree_json(self):
        return interchange.node_json('input', {'value': self._value}, [])
    def handle_interaction(self, interaction):
        if interaction.type == 'input':
            self.value = interaction.value

    @property
    def value(self) -> str:
        return self._value
    @value.setter
    def value(self, value: str) -> None:
        self._value = value
        if self._callback is not None:
            self._callback(value)
        self.mark_dirty()
