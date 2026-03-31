import json
import logging
from aiohttp import web
from app.browser.manager import browser_manager
from app.config import Config

logger = logging.getLogger(__name__)


async def browse_handler(request: web.Request) -> web.Response:
    session_id = request.query.get('session', 'default')
    data = await request.json()
    action = data.get('action')
    
    try:
        session = browser_manager.get_session(session_id)
        
        if action == 'create':
            await session.start()
            return web.json_response({'session': session_id})
        
        elif action == 'navigate':
            if not session.browser:
                await session.start()
            url = data.get('url')
            await session.navigate(url)
            return web.json_response({'ok': True})
        
        elif action == 'evaluate':
            if not session.browser:
                raise RuntimeError('No session')
            script = data.get('script')
            result = await session.evaluate(script)
            return web.json_response(result)

        elif action == "screenshot":
            if not session.browser:
                await session.start()
            quality = data.get("quality", Config.SCREENSHOT_QUALITY)
            viewport_width = data.get("width", session.viewport_width)
            viewport_height = data.get("height", session.viewport_height)

            if (
                viewport_width != session.viewport_width
                or viewport_height != session.viewport_height
            ):
                await session.set_viewport_size(viewport_width, viewport_height)

            screenshot_bytes = await session.capture_frame(quality=quality)
            if screenshot_bytes:
                return web.Response(
                    body=screenshot_bytes,
                    content_type="image/jpeg",
                    headers={"Content-Disposition": "inline"},
                )
            else:
                return web.json_response({"error": "Screenshot failed"}, status=500)

        elif action == "close":
            await browser_manager.close_session(session_id)
            return web.json_response({'ok': True})
        
        else:
            return web.json_response({'error': 'Unknown action'}, status=400)
            
    except Exception as e:
        logger.error(f'Browser error: {e}')
        return web.json_response({'error': str(e)}, status=500)


def setup_http_handlers(app: web.Application):
    app.router.add_post('/browse', browse_handler)
