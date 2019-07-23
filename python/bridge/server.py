import asyncio
import functools
import socket
import threading
import time
import webbrowser

from pathlib import Path
from typing import Iterable, MutableSet, Optional, Sequence, Set, TypeVar

from aiohttp import web

from .gui import AbstractGUI
from .interchange import Interaction, poll_response

CLIENT_HTML = Path(__file__).absolute().parent.parent.parent / 'elm-client' / 'index.html'
assert CLIENT_HTML.is_file()

_T = TypeVar('_T')
def _union(xss: Iterable[Iterable[_T]]) -> Set[_T]:
    result: MutableSet[_T] = set()
    for xs in xss:
        result |= set(xs)
    return set(result)

async def index(request: web.Request) -> web.FileResponse:
    return web.FileResponse(CLIENT_HTML)

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
    gui: AbstractGUI, condition: asyncio.Condition) -> Sequence[web.RouteDef]:
    return [
        web.RouteDef(method='GET', path='/', handler=index, kwargs={}),
        web.RouteDef(method='POST', path='/poll', handler=functools.partial(poll, gui=gui, condition=condition), kwargs={}),
        web.RouteDef(method='POST', path='/interaction', handler=functools.partial(interaction, gui=gui, condition=condition), kwargs={}),
    ]

def _get_open_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    port = s.getsockname()[1]
    s.close()
    return port
def _open_page_soon(url: str, delay_sec: float = 0.1) -> None:
    def f() -> None:
        time.sleep(delay_sec)
        webbrowser.open(url)
    threading.Thread(target=f).start()

def serve(
    gui: AbstractGUI,
    *,
    loop: Optional[asyncio.AbstractEventLoop] = None,
    host: str = 'localhost',
    port: Optional[int] = None,
    open_browser: bool = True,
) -> None:
    loop_ = loop if (loop is not None) else asyncio.get_event_loop()
    condition = asyncio.Condition(loop=loop_)
    async def notify_all():
        async with condition:
            condition.notify_all()
    gui.add_listener(lambda: asyncio.run_coroutine_threadsafe(notify_all(), loop_))
    app = web.Application(loop=loop_)
    app.add_routes(build_routes(gui=gui, condition=condition))
    if port is None:
        port = _get_open_port()
    if open_browser:
        _open_page_soon(f'http://localhost:{port}')
    web.run_app(app, host=host, port=port)
