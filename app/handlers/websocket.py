import json
import logging
from aiohttp import web
from app.browser.manager import browser_manager
from app.webrtc.peer import WebRTCPeer

logger = logging.getLogger(__name__)


async def websocket_handler(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    session_id = request.query.get('session', 'default')
    peer_id = f'{session_id}-{id(request)}'
    
    logger.info(f'WebSocket connected: {peer_id}')
    
    peer = WebRTCPeer(session_id, ws)
    
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    msg_type = data.get('type')
                    
                    if msg_type == 'offer':
                        await peer.handle_offer(data)
                        
                    elif msg_type == 'candidate':
                        await peer.handle_ice_candidate(data)
                        
                    elif msg_type == 'start':
                        url = data.get('url', 'https://example.com')
                        
                        session = browser_manager.get_session(session_id)
                        await session.start()
                        await session.navigate(url)
                        
                        await peer.start_streaming(session)
                        
                except json.JSONDecodeError:
                    logger.error(f'Invalid JSON from {peer_id}')
                    
            elif msg.type == web.WSMsgType.ERROR:
                logger.error(f'WebSocket error: {ws.exception()}')
                
    finally:
        logger.info(f'WebSocket closed: {peer_id}')
        await peer.close()
        
    return ws


def setup_websocket_handlers(app: web.Application):
    app.router.add_get('/ws', websocket_handler)
