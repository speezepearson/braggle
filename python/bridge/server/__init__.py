import asyncio
import base64
import functools
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

CLIENT_HTML = Path(__file__).absolute().parent.parent.parent.parent / 'elm-client' / 'index.html'
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

    loop_: asyncio.AbstractEventLoop = loop if (loop is not None) else asyncio.get_event_loop()
    del loop

    condition = asyncio.Condition(loop=loop_)

    async def notify_all():
        async with condition:
            condition.notify_all()
    gui.add_listener(lambda: asyncio.run_coroutine_threadsafe(notify_all(), loop_))
    app = web.Application(loop=loop_, middlewares=[_auth.build_middleware(token=token)])
    app.add_routes(_auth.build_routes(token=token))
    app.add_routes(Server(gui, condition).build_routes())

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
