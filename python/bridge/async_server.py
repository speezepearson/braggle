import asyncio
import functools

from pathlib import Path
from typing import Iterable, MutableSet, Sequence, Set, TypeVar

from aiohttp import web

from .gui import AsyncGUI
from .interchange import Interaction, poll_response

_T = TypeVar('_T')
def _union(xss: Iterable[Iterable[_T]]) -> Set[_T]:
    result: MutableSet[_T] = set()
    for xs in xss:
        result |= set(xs)
    return set(result)

async def index(request: web.Request, client_html: Path) -> web.FileResponse:
    return web.FileResponse(client_html)

async def poll(request: web.Request, gui: AsyncGUI) -> web.Response:
    since = await request.json()
    async with gui.dirtied:
        await gui.dirtied.wait_for(lambda: gui.time_step > since)
        t = gui.time_step
        recently_dirtied = set(gui.get_dirtied_elements(start=since, end=t))
        return web.json_response(poll_response(
            root=gui.root,
            time_step=t,
            elements=_union(e.walk() for e in recently_dirtied),
        ))

async def interaction(request: web.Request, gui: AsyncGUI) -> web.Response:
    j = await request.json()
    async with gui.dirtied:
        for element in gui.root.walk():
            if element.id == j['target']:
                element.handle_interaction(Interaction(**j))
                return web.Response(text='ok')
        return web.Response(status=404)

def build_routes(gui: AsyncGUI, client_html: Path) -> Sequence[web.RouteDef]:
    return [
        web.RouteDef(method='GET', path='/', handler=functools.partial(index, client_html=client_html), kwargs={}),
        web.RouteDef(method='POST', path='/poll', handler=functools.partial(poll, gui=gui), kwargs={}),
        web.RouteDef(method='POST', path='/interaction', handler=functools.partial(interaction, gui=gui), kwargs={}),
    ]

def serve(gui: AsyncGUI, client_html: Path) -> None:
    loop = asyncio.get_event_loop()
    app = web.Application(loop=loop)
    app.add_routes(build_routes(gui=gui, client_html=client_html))
    web.run_app(app, port=4392)
