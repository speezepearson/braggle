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

def build_server_app(
    gui: AbstractGUI,
    *,
    token: str,
    loop: Optional[asyncio.AbstractEventLoop] = None,
) -> web.Application:

    loop_: asyncio.AbstractEventLoop = loop if (loop is not None) else asyncio.get_event_loop()
    del loop

    condition = asyncio.Condition(loop=loop_)

    async def notify_all():
        async with condition:
            condition.notify_all()
    gui.add_listener(lambda: asyncio.run_coroutine_threadsafe(notify_all(), loop_))
    app = web.Application(loop=loop_, middlewares=[_auth.build_middleware(token=token)])
    app.add_routes(_auth.build_routes(token=token))
    app.add_routes(build_routes(gui=gui, condition=condition))

    return app

import functools
functools.wraps(build_server_app, assigned=['__annotations__'])
async def serve_async(
    *args,
    host: str = 'localhost',
    port: Optional[int] = None,
    token: Optional[str] = None,
    open_browser: bool = True,
    **kwargs,
) -> None:
    token_: str = token if (token is not None) else _auth.generate_token()
    del token
    port_: int = port if (port is not None) else _get_open_port()
    del port

    app = build_server_app(*args, token=token_, **kwargs)

    url = f'http://{host}:{port_}/auth/{token_}'
    print('serving on:', url) # TODO: figure out a better way to yield this information; logging?
    if open_browser:
        async def _open_browser(_):
            webbrowser.open(url)
        app.on_startup.append(_open_browser)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port_)
    await site.start()
    try:
        await asyncio.sleep(1e10)
    finally:
        await runner.cleanup()

functools.wraps(serve_async, assigned=['__annotations__'])
def serve(*args, **kwargs) -> None:
    asyncio.run(serve_async(*args, **kwargs))
