import asyncio
import functools

from pathlib import Path
from typing import Iterable, MutableSet, Optional, Sequence, Set, TypeVar

from aiohttp import web

from .gui import AbstractGUI
from .interchange import Interaction, poll_response

_T = TypeVar('_T')
def _union(xss: Iterable[Iterable[_T]]) -> Set[_T]:
    result: MutableSet[_T] = set()
    for xs in xss:
        result |= set(xs)
    return set(result)

async def index(request: web.Request, client_html: Path) -> web.FileResponse:
    return web.FileResponse(client_html)

async def poll(request: web.Request, gui: AbstractGUI, condition: asyncio.Condition) -> web.Response:
    since = await request.json()
    async with condition:
        await condition.wait_for(lambda: gui.time_step > since)
        return web.json_response(gui.render_poll_response(since=since))

async def interaction(request: web.Request, gui: AbstractGUI, condition: asyncio.Condition) -> web.Response:
    j = await request.json()
    async with condition:
        for element in gui.root.walk():
            if element.id == j['target']:
                element.handle_interaction(Interaction(**j))
                return web.Response(text='ok')
        return web.Response(status=404)

def build_routes(
    gui: AbstractGUI, client_html: Path, condition: asyncio.Condition) -> Sequence[web.RouteDef]:
    return [
        web.RouteDef(method='GET', path='/', handler=functools.partial(index, client_html=client_html), kwargs={}),
        web.RouteDef(method='POST', path='/poll', handler=functools.partial(poll, gui=gui, condition=condition), kwargs={}),
        web.RouteDef(method='POST', path='/interaction', handler=functools.partial(interaction, gui=gui, condition=condition), kwargs={}),
    ]

def serve(gui: AbstractGUI, client_html: Path, *, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
    loop_ = loop if (loop is not None) else asyncio.get_event_loop()
    condition = asyncio.Condition(loop=loop_)
    async def notify_all():
        async with condition:
            condition.notify_all()
    gui.add_listener(lambda: asyncio.run_coroutine_threadsafe(notify_all(), loop_))
    app = web.Application(loop=loop_)
    app.add_routes(build_routes(gui=gui, client_html=client_html, condition=condition))
    web.run_app(app, port=4392)
