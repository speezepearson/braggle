import asyncio
import base64
import functools
import socket
import time
import webbrowser

from pathlib import Path
from typing import Iterable, MutableSet, Optional, Sequence, Set, Tuple, TypeVar, Callable, Awaitable

from aiohttp import web

from ..gui import AbstractGUI
from ..interchange import Interaction, poll_response
from . import _auth

CLIENT_HTML = Path(__file__).absolute().parent.parent.parent.parent / 'elm-client' / 'index.html'
assert CLIENT_HTML.is_file()

_T = TypeVar('_T')
def _union(xss: Iterable[Iterable[_T]]) -> Set[_T]:
    result: MutableSet[_T] = set()
    for xs in xss:
        result |= set(xs)
    return set(result)

async def index(
    request: web.Request,
) -> web.FileResponse:
    return web.FileResponse(CLIENT_HTML)

async def poll(
    request: web.Request,
    gui: AbstractGUI,
    condition: asyncio.Condition,
) -> web.Response:
    since = await request.json()
    async with condition:
        await condition.wait_for(lambda: gui.time_step > since)
        return web.json_response(gui.render_poll_response(since=since))

async def interaction(
    request: web.Request,
    gui: AbstractGUI,
    condition: asyncio.Condition,
) -> web.Response:
    j = await request.json()
    async with condition:
        for element in gui.root.walk():
            if element.id == j['target']:
                element.handle_interaction(Interaction(**j))
                return web.Response(text='ok')
        return web.Response(status=404)

def build_routes(
    gui: AbstractGUI,
    condition: asyncio.Condition,
) -> Sequence[web.RouteDef]:
    return [
        web.RouteDef(method='GET', path=f'/', handler=index, kwargs={}),
        web.RouteDef(method='POST', path=f'/poll', handler=functools.partial(poll, gui=gui, condition=condition), kwargs={}),
        web.RouteDef(method='POST', path=f'/interaction', handler=functools.partial(interaction, gui=gui, condition=condition), kwargs={}),
    ]

def _get_open_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def serve(
    gui: AbstractGUI,
    *,
    loop: Optional[asyncio.AbstractEventLoop] = None,
    host: str = 'localhost',
    port: Optional[int] = None,
    open_browser: bool = True,
    token: Optional[str] = None
) -> None:

    loop = loop if (loop is not None) else asyncio.get_event_loop()
    port = port if (port is not None) else _get_open_port()
    token = token if (token is not None) else _auth.generate_token()

    condition = asyncio.Condition(loop=loop)

    async def notify_all():
        async with condition:
            condition.notify_all()
    gui.add_listener(lambda: asyncio.run_coroutine_threadsafe(notify_all(), loop))
    app = web.Application(loop=loop, middlewares=[_auth.build_middleware(token=token)])
    app.add_routes(_auth.build_routes(token=token))
    app.add_routes(build_routes(gui=gui, condition=condition))
    url = f'http://localhost:{port}/auth/{token}'
    if open_browser:
        async def _open_browser(_):
            print('serving on:', url) # TODO: figure out a better way to yield this information; logging?
            webbrowser.open(url)
        app.on_startup.append(_open_browser)
    web.run_app(app, host=host, port=port)
