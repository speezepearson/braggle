from __future__ import annotations

import asyncio

from pathlib import Path
from typing import MutableSequence, TYPE_CHECKING

from aiohttp import web

from .interchange import Interaction

if TYPE_CHECKING:
    from .element import Element

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

    def run(self, client_html: Path) -> None:
        routes = web.RouteTableDef()
        @routes.get('/')
        async def index(request: web.Request) -> web.FileResponse:
            #import time; time.sleep(1)
            return web.FileResponse(client_html)
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
                    if element.id == j['target']:
                        element.handle_interaction(Interaction(**j))
                        return web.Response(text='ok')
                return web.Response(status=404)
        app = web.Application(loop=self._loop)
        app.add_routes(routes)
        web.run_app(app, port=4392)
