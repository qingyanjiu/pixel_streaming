import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


class Config:
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8080"))

    ICE_SERVERS = [
        {"urls": ["stun:stun.l.google.com:19302"]},
    ]

    TURN_SERVER = os.getenv("TURN_SERVER", "")
    TURN_PORT = int(os.getenv("TURN_PORT", "8888"))
    TURN_USER = os.getenv("TURN_USER", "")
    TURN_PASSWORD = os.getenv("TURN_PASSWORD", "")

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
