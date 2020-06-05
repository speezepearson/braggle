import asyncio
import base64
import functools
import secrets
import socket
import time
import webbrowser

from pathlib import Path
from typing import Iterable, MutableSet, Optional, Sequence, Set, Tuple, TypeVar, Callable, Awaitable

from aiohttp import web

from ..element import Element
from ..gui import AbstractGUI
from ..protobuf import element_pb2
from ..types import ElementId
from . import _auth

CLIENT_HTML = (Path(__file__).parent / 'static' / 'index.html').resolve()
assert CLIENT_HTML.is_file()

_T = TypeVar('_T')
def _union(xss: Iterable[Iterable[_T]]) -> Set[_T]:
    result: MutableSet[_T] = set()
    for xs in xss:
        result |= set(xs)
    return set(result)

class Server:
    def __init__(self, gui: AbstractGUI, condition: asyncio.Condition):
        self.gui = gui
        self.condition = condition

    def build_routes(self) -> Sequence[web.RouteDef]:
        return [
            web.get('/', self.index),
            web.post('/poll', self.poll),
            web.post('/interaction', self.interaction),
        ]

    async def index(self, request: web.BaseRequest) -> web.StreamResponse:
        return web.FileResponse(CLIENT_HTML)

    async def poll(self, request: web.BaseRequest) -> web.StreamResponse:
        request_pb = element_pb2.PollRequest.FromString(await request.content.read())
        since = request_pb.since_timestep
        async with self.condition:
            await self.condition.wait_for(lambda: self.gui.time_step > since)
            return web.Response(
                status=200,
                content_type="application/octet_stream",
                body=element_pb2.PollResponse(state=self.gui.updates_since(since)).SerializeToString(),
            )

    async def interaction(self, request: web.BaseRequest) -> web.StreamResponse:
        bs = await request.content.read()
        request_pb = element_pb2.InteractionRequest.FromString(bs)
        interaction = request_pb.interaction
        async with self.condition:
            _dispatch_event_or_404(self.gui.root, interaction)

        return web.Response(
            status=200,
            content_type="application/octet_stream",
            body=element_pb2.InteractionResponse().SerializeToString(),
        )

def _dispatch_event_or_404(root: Element, interaction: element_pb2.Interaction) -> None:
    if interaction.WhichOneof("interaction_kind") == "click":
        click_event = interaction.click
        _find_element_or_404(root, ElementId(click_event.element_id)).handle_click(click_event)
    elif interaction.WhichOneof("interaction_kind") == "text_input":
        text_input_event = interaction.text_input
        _find_element_or_404(root, ElementId(text_input_event.element_id)).handle_text_input(text_input_event)
    else:
        raise ValueError("unknown kind of interaction", interaction.WhichOneof("interaction_kind"))

def _find_element_or_404(root: Element, id: ElementId) -> Element:
    result = next((e for e in root.walk() if e.id == id), None)
    if result is None:
        raise web.HTTPNotFound(body=id)
    return result

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

    if loop is None:
        loop = asyncio.get_event_loop()
        if loop is None:
            raise RuntimeError("can't get my hands on an event loop")
    _mandatory_loop = loop  # mypy hack to make it realize this variable is effectively final

    condition = asyncio.Condition(loop=loop)

    async def notify_all():
        async with condition:
            condition.notify_all()
    gui.add_listener(lambda: asyncio.run_coroutine_threadsafe(notify_all(), _mandatory_loop))
    app = web.Application(loop=loop, middlewares=[_auth.build_middleware(token=token)])
    app.add_routes(_auth.build_routes(token=token))
    app.add_routes(Server(gui, condition).build_routes())

    return app

async def serve_async(
    gui: AbstractGUI,
    *,
    host: str = 'localhost',
    port: Optional[int] = None,
    token: Optional[str] = None,
    open_browser: bool = True,
    loop: Optional[asyncio.AbstractEventLoop] = None,
) -> None:
    if token is None:
        token = secrets.token_urlsafe(32)
    if port is None:
        port = _get_open_port()

    app = build_server_app(gui=gui, token=token, loop=loop)

    url = f'http://{host}:{port}/auth/{token}'
    print('serving on:', url) # TODO: figure out a better way to yield this information
    if open_browser:
        async def _open_browser(_):
            webbrowser.open(url)
        app.on_startup.append(_open_browser)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    try:
        await asyncio.sleep(1e10)
    finally:
        await runner.cleanup()

functools.wraps(serve_async, assigned=['__annotations__'])
def serve(*args, **kwargs) -> None:
    asyncio.run(serve_async(*args, **kwargs))
