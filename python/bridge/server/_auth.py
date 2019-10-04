import asyncio
import base64
import functools
import socket
import time
import webbrowser

from pathlib import Path
from typing import Iterable, MutableSet, Optional, Sequence, Set, Tuple, TypeVar, Callable, Awaitable

from aiohttp import web

async def _redirect_to_index(request: web.Request) -> web.Response:
    result = web.HTTPPermanentRedirect('/')
    return result

def build_middleware(
    token: str,
):
    @web.middleware
    async def middleware(
        request: web.Request,
        handler: Callable[[web.Request], Awaitable[web.Response]],
    ) -> web.Response:
        if request.path == f'/auth/{token}':
            result = await handler(request)
            result.set_cookie('token', token)
            return result
        if request.cookies.get('token') != token:
            raise web.HTTPForbidden(reason='bad/no auth token')
        return await handler(request)
    return middleware

def build_routes(
    token: str,
) -> Sequence[web.RouteDef]:
    return [
        web.RouteDef(method='GET', path=f'/auth/{token}', handler=_redirect_to_index, kwargs={}),
    ]

def generate_token() -> str:
    with open('/dev/urandom', 'rb') as f:
        return base64.b64encode(f.read(32), b'-_').decode('utf8').rstrip('=')
