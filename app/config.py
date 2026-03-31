import os
from pathlib import Path
from configparser import ConfigParser


def _load_ini_config():
    ini_path = Path(__file__).parent.parent / "config.ini"
    parser = ConfigParser()
    if ini_path.exists():
        parser.read(ini_path)
        return parser
    return None


class Config:
    _ini_config = _load_ini_config()

    HOST = "0.0.0.0"
    PORT = 8080
    VIEWPORT_WIDTH = 1920
    VIEWPORT_HEIGHT = 1080
    SCREENSHOT_QUALITY = 80
    STREAM_FPS = 15
    TURN_SERVER = ""
    TURN_PORT = 19303
    TURN_USER = ""
    TURN_PASSWORD = ""

    ICE_SERVERS = [
        {"urls": ["stun:stun.l.google.com:19302"]},
    ]

    if _ini_config:
        if _ini_config.has_section("server"):
            HOST = _ini_config.get("server", "host", fallback=HOST)
            PORT = int(_ini_config.get("server", "port", fallback=PORT))

        if _ini_config.has_section("settings"):
            VIEWPORT_WIDTH = int(
                _ini_config.get("settings", "viewport_width", fallback=VIEWPORT_WIDTH)
            )
            VIEWPORT_HEIGHT = int(
                _ini_config.get("settings", "viewport_height", fallback=VIEWPORT_HEIGHT)
            )
            SCREENSHOT_QUALITY = int(
                _ini_config.get(
                    "settings", "screenshot_quality", fallback=SCREENSHOT_QUALITY
                )
            )
            STREAM_FPS = int(
                _ini_config.get("settings", "stream_fps", fallback=STREAM_FPS)
            )

        if _ini_config.has_section("turn"):
            TURN_SERVER = _ini_config.get("turn", "server", fallback=TURN_SERVER)
            TURN_PORT = int(_ini_config.get("turn", "port", fallback=TURN_PORT))
            TURN_USER = _ini_config.get("turn", "user", fallback=TURN_USER)
            TURN_PASSWORD = _ini_config.get("turn", "password", fallback=TURN_PASSWORD)

    @classmethod
    def get_ice_servers(cls):
        servers = list(cls.ICE_SERVERS)
        if cls.TURN_SERVER:
            turn_url = f"turn:{cls.TURN_SERVER}:{cls.TURN_PORT}"
            if cls.TURN_USER:
                servers.append(
                    {
                        "urls": [turn_url],
                        "username": cls.TURN_USER,
                        "credential": cls.TURN_PASSWORD,
                    }
                )
            else:
                servers.append({"urls": [turn_url]})
        return servers
