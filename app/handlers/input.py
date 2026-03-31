import json
import logging
from aiohttp import web
from app.browser.manager import browser_manager
from app.config import Config

logger = logging.getLogger(__name__)

REMOTE_VIEWPORT_WIDTH = 1920
REMOTE_VIEWPORT_HEIGHT = 1080


async def input_handler(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    session_id = request.query.get("session", "default")
    logger.info(f"Input control connected: {session_id}")

    session = browser_manager.get_session(session_id)

    if not session.page:
        await session.start()

    await session.set_viewport_size(REMOTE_VIEWPORT_WIDTH, REMOTE_VIEWPORT_HEIGHT)

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    event_type = data.get("type")

                    if event_type == "mouse":
                        action = data.get("action")
                        ratio_x = data.get("x", 0)
                        ratio_y = data.get("y", 0)
                        x = ratio_x * REMOTE_VIEWPORT_WIDTH
                        y = ratio_y * REMOTE_VIEWPORT_HEIGHT
                        button = data.get("button", "left")

                        if action == "move":
                            await session.mouse_move(x, y)
                        elif action == "click":
                            await session.mouse_click(x, y, button=button)
                        elif action == "dblclick":
                            await session.mouse_click(x, y, click_count=2)
                        elif action == "down":
                            await session.mouse_move(x, y)
                            await session.mouse_down(button=button)
                        elif action == "up":
                            await session.mouse_up(button=button)
                        elif action == "wheel":
                            delta_x = data.get("deltaX", 0)
                            delta_y = data.get("deltaY", 0)
                            await session.mouse_wheel(delta_x, delta_y)

                    elif event_type == "keyboard":
                        action = data.get("action")
                        key = data.get("key", "")

                        if action == "down":
                            await session.keyboard_down(key)
                        elif action == "up":
                            await session.keyboard_up(key)
                        elif action == "press":
                            await session.keyboard_press(key)

                    elif event_type == "text":
                        action = data.get("action")
                        text = data.get("text", "")

                        if action == "input" and text:
                            await session.keyboard_type(text)

                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from input control")
                except Exception as e:
                    logger.error(f"Input error: {e}")

            elif msg.type == web.WSMsgType.ERROR:
                logger.error(f"WebSocket error: {ws.exception()}")

    finally:
        logger.info(f"Input control disconnected: {session_id}")

    return ws


def setup_input_handlers(app: web.Application):
    app.router.add_get("/input", input_handler)
