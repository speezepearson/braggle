from __future__ import annotations

import asyncio

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Iterable, MutableSequence, MutableSet, Optional, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from .element import Element
    from .interchange import BridgeJson, PollResponse

class AbstractGUI(ABC):
    @property
    @abstractmethod
    def root(self) -> Element:
        '''...'''

    @abstractmethod
    def mark_dirty(self, element: Element) -> None:
        '''...'''

    @property
    @abstractmethod
    def time_step(self) -> int:
        '''...'''

    @abstractmethod
    def get_dirtied_elements(self, start: int = 0, end: Optional[int] = None) -> Iterable[Element]:
        '''...'''

    @abstractmethod
    def add_listener(self, listener: Callable[[], Any]) -> None:
        '''TODO(spencerpearson): this is awkward and weird.'''

class GUI(AbstractGUI):
    def __init__(self, root: Element) -> None:
        self._root = root
        self._root.gui = self
        self._dirty_elements = [root]
        self._mark_dirty_listeners: MutableSet[Callable[[], Any]] = set()

    @property
    def root(self) -> Element:
        return self._root

    def mark_dirty(self, element: Element) -> None:
        self._dirty_elements.append(element)
        for listener in self._mark_dirty_listeners:
            listener()

    @property
    def time_step(self) -> int:
        return len(self._dirty_elements)

    def get_dirtied_elements(self, start: int = 0, end: Optional[int] = None) -> Iterable[Element]:
        return self._dirty_elements[start : end]

    def add_listener(self, listener: Callable[[], None]) -> None:
        self._mark_dirty_listeners.add(listener)
