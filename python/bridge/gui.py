from __future__ import annotations

import asyncio

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, MutableSequence, Optional, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from .element import Element
    from .interchange import BridgeJson, PollResponse

class GUI(ABC):
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

class AsyncGUI(GUI):
    def __init__(self, root: Element, *, loop: asyncio.AbstractEventLoop = None) -> None:
        self._loop = loop if (loop is not None) else asyncio.get_event_loop()
        self._root = root
        self._dirty_elements: MutableSequence[Element] = [root]
        self._dirtied = asyncio.Condition(loop=loop)
        self._root.gui = self

    @property
    def root(self) -> Element:
        return self._root

    @property
    def time_step(self) -> int:
        return len(self._dirty_elements)

    @property
    def dirtied(self) -> asyncio.Condition:
        return self._dirtied

    def get_dirtied_elements(self, start: int = 0, end: Optional[int] = None) -> Iterable[Element]:
        return self._dirty_elements[start:end]

    async def _mark_dirty_async(self, element: Element) -> None:
        async with self._dirtied:
            self._dirty_elements.append(element)
            self._dirtied.notify_all()

    def mark_dirty(self, element: Element) -> None:
        self._loop.create_task(self._mark_dirty_async(element))
