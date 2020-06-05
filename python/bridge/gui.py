from __future__ import annotations

import asyncio

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Iterable, MutableSequence, MutableSet, Optional, Sequence, TYPE_CHECKING

from .element import Element, Container
from .protobuf import element_pb2
from .types import TimeStep

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
    def updates_since(self, since: int = 0) -> element_pb2.PartialServerState:
        '''...'''

    @abstractmethod
    def add_listener(self, listener: Callable[[], Any]) -> None:
        '''TODO: this is awkward and weird.'''

class GUI(AbstractGUI):
    '''Not thread-safe.'''
    def __init__(self, *children: Element) -> None:
        self._root = Container(children)
        self._root.gui = self
        self._dirty_elements: MutableSequence[Element] = list(self._root.walk())
        self._mark_dirty_listeners: MutableSet[Callable[[], Any]] = set()

    @property
    def root(self) -> Element:
        return self._root

    def mark_dirty(self, element: Element) -> None:
        self._dirty_elements.append(element)
        for listener in self._mark_dirty_listeners:
            listener()

    @property
    def time_step(self) -> TimeStep:
        return TimeStep(len(self._dirty_elements))

    def updates_since(self, since: int = 0) -> element_pb2.PartialServerState:
        since = max(since, 0)
        recently_dirtied = set(self._dirty_elements[since:])
        return element_pb2.PartialServerState(
            root_id=self.root.id,
            timestep=self.time_step,
            elements={e.id: e.to_protobuf() for e in recently_dirtied},
        )

    def add_listener(self, listener: Callable[[], None]) -> None:
        self._mark_dirty_listeners.add(listener)
