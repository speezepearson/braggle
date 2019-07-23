from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod, abstractproperty
from dataclasses import dataclass
from typing import Any, Callable, Iterator, Mapping, MutableSequence, NewType, Optional, Sequence, Tuple, Union

from aiohttp import web

@dataclass(frozen=True)
class Interaction:
    target: str
    type: str
    value: Optional[str] = None

BridgeJson = NewType('BridgeJson', Mapping[str, Any])

def bridge_text_json(s: str) -> BridgeJson:
    return BridgeJson({'text': s})
def bridge_node_json(
    node_name: str,
    attributes: Mapping[str, str],
    children: Sequence[Union[BridgeJson, Element]]
) -> BridgeJson:
    return BridgeJson({
        'name': node_name,
        'attributes': attributes,
        'children': [{'ref': c.id} if isinstance(c, Element) else c for c in children],
    })

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
        self._gui: Optional[GUI] = None

    @property
    def parent(self) -> Optional[Element]:
        return self._parent
    @parent.setter
    def parent(self, parent: Element) -> None:
        if (self._parent is not None) and (parent is not None):
            raise RuntimeError('cannot set parent of Element that already has a parent')
        self._parent = parent

    @property
    def children(self) -> Sequence[Element]:
        return ()

    def walk(self) -> Iterator[Element]:
        yield self
        for child in self.children:
            yield from child.walk()

    @property
    def gui(self) -> Optional[GUI]:
        if self._gui is not None:
            return self._gui
        if self.parent is not None:
            return self.parent.gui
        return None
    @gui.setter
    def gui(self, gui: GUI) -> None:
        if self.parent is not None:
            raise RuntimeError('cannot set GUI of an Element that has a parent')
        self._gui = gui

    def mark_dirty(self) -> None:
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
        return bridge_node_json(
            'ul',
            {},
            [bridge_node_json('li', {}, [child])
             for child in self._children],
        )

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
        return bridge_text_json(self.text)
    def handle_interaction(self, interaction):
        if interaction.type == 'click':
            self._callback()

class Button(Element):
    def __init__(self, text: str, callback: Callable[[], None], **kwargs) -> None:
        super().__init__(**kwargs)
        self._text = text
        self._callback = callback
    def subtree_json(self):
        return bridge_node_json('button', {}, [bridge_text_json(self._text)])
    def handle_interaction(self, interaction):
        if interaction.type == 'click':
            self._callback()

class TextField(Element):
    def __init__(self, callback: Callable[[str], None], **kwargs) -> None:
        super().__init__(**kwargs)
        self._value = ''
        self._callback = callback
    def subtree_json(self):
        return bridge_node_json('input', {'value': self._value}, [])
    def handle_interaction(self, interaction):
        if interaction.type == 'input':
            self._callback(interaction.value)

    @property
    def value(self) -> str:
        return self._value
    @value.setter
    def value(self, value: str) -> None:
        self._value = value
        self.mark_dirty()

class GUI:
    def __init__(self, loop: asyncio.AbstractEventLoop, root: Element) -> None:
        self._loop = loop
        self._root = root
        self._dirty_elements: MutableSequence[Element] = []
        self._dirtied = asyncio.Condition()
        self._root.gui = self

    @property
    def time_step(self) -> int:
        return len(self._dirty_elements)

    async def _mark_dirty_async(self, element: Element) -> None:
        async with self._dirtied:
            self._dirty_elements.append(element)
            self._dirtied.notify_all()
    def mark_dirty(self, element: Element) -> None:
        asyncio.run_coroutine_threadsafe(self._mark_dirty_async(element), self._loop)

    def run(self):
        routes = web.RouteTableDef()
        @routes.get('/')
        async def index(request: web.Request) -> web.FileResponse:
            #import time; time.sleep(1)
            return web.FileResponse('elm-client/index.html')
        @routes.post('/poll')
        async def poll(request: web.Request) -> web.Response:
            #import time; time.sleep(1)
            since = await request.json()
            async with self._dirtied:
                await self._dirtied.wait_for(lambda: self.time_step > since)
                recently_dirtied = set(self._dirty_elements[since:])
                return web.json_response({
                    'root': self._root.id,
                    'timeStep': self.time_step,
                    'elements': {
                        e.id: {"id": e.id, "subtree": e.subtree_json()}
                        for e in self._root.walk()
                    },
                })
        @routes.post('/interaction')
        async def interaction(request: web.Request) -> web.Response:
            #import time; time.sleep(1)
            j = await request.json()
            async with self._dirtied:
                for element in self._root.walk():
                    if isinstance(element, Element) and element.id == j['target']:
                        element.handle_interaction(Interaction(**j))
                        return web.Response(text='ok')
                return web.Response(status=404)
        app = web.Application(loop=self._loop)
        app.add_routes(routes)
        web.run_app(app, port=4392)

t = Text('foo')
def callback():
    t.text = t.text + '!'
b = Button(text='click', callback=callback)

def callback2(s): t2.text = s
t2 = Text('')
tf = TextField(callback=callback2)
GUI(
    loop=asyncio.get_event_loop(),
    root=List([t, b, t2, tf]),
).run()
