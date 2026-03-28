import json
import logging
from aiohttp import web
from app.browser.manager import browser_manager

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
        
        elif action == 'close':
            await browser_manager.close_session(session_id)
            return web.json_response({'ok': True})
        
        else:
            return web.json_response({'error': 'Unknown action'}, status=400)
            
    except Exception as e:
        logger.error(f'Browser error: {e}')
        return web.json_response({'error': str(e)}, status=500)


def setup_http_handlers(app: web.Application):
    app.router.add_post('/browse', browse_handler)
