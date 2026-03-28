import asyncio
import logging
from aiohttp import web
from pathlib import Path

from app.handlers.http import setup_http_handlers
from app.handlers.websocket import setup_websocket_handlers

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_app() -> web.Application:
    app = web.Application()
    
    app.router.add_get('/', self_static)
    app.router.add_static('/static/', path=Path(__file__).parent.parent / 'web' / 'public', name='static')
    
    setup_http_handlers(app)
    setup_websocket_handlers(app)
    
    return app


async def self_static(request):
    index_path = Path(__file__).parent.parent / 'web' / 'public' / 'index.html'
    return web.FileResponse(index_path)


def main():
    app = asyncio.run(create_app())
    web.run_app(app, host='0.0.0.0', port=8080)


if __name__ == '__main__':
    main()
