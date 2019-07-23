from __future__ import annotations

import asyncio

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Iterable, MutableSequence, MutableSet, Optional, Sequence, TYPE_CHECKING

from .interchange import BridgeJson, PollResponse, poll_response

if TYPE_CHECKING:
    from .element import Element

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
    def render_poll_response(self, since: int = 0) -> PollResponse:
        '''...'''

    @abstractmethod
    def add_listener(self, listener: Callable[[], Any]) -> None:
        '''TODO: this is awkward and weird.'''

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

    def render_poll_response(self, since: int = 0) -> PollResponse:
        recently_dirtied = set(self._dirty_elements[since:])
        return poll_response(
            root=self.root,
            time_step=self.time_step,
            elements=set().union(*(e.walk() for e in recently_dirtied)), # type: ignore
        )
        # TODO: don't walk the whole tree from each modified element;
        #   instead, keep track of when elements are added from the tree,
        #   so that we don't have to walk the tree to ensure we get all the added elements

    def add_listener(self, listener: Callable[[], None]) -> None:
        self._mark_dirty_listeners.add(listener)
