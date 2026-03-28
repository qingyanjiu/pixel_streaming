import asyncio
import json
import logging
import av
import numpy as np
from typing import Optional
from aiohttp import web
from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    RTCConfiguration,
    RTCIceServer,
    VideoStreamTrack,
)
from aiortc.contrib.media import MediaBlackhole
from aiortc import rtcpeerconnection, sdp
from app.config import Config

logger = logging.getLogger(__name__)

ORIGINAL_AND_DIRECTION = rtcpeerconnection.and_direction


def safe_and_direction(a, b):
    if a is None or b is None:
        return None
    try:
        return ORIGINAL_AND_DIRECTION(a, b)
    except (ValueError, IndexError):
        return None


rtcpeerconnection.and_direction = safe_and_direction


class BrowserVideoTrack(VideoStreamTrack):
    def __init__(self, browser_session):
        super().__init__()
        self.browser_session = browser_session
        self.frame_count = 0

    async def recv(self):
        pts, time_base = await self.next_timestamp()

        frame_data = await self.browser_session.capture_frame()

        if frame_data is None:
            await asyncio.sleep(0.1)
            return await self.recv()

        try:
            import io

            with av.open(io.BytesIO(frame_data)) as container:
                packet = next(container.demux())
                frame = packet.decode()[0]
                frame = frame.to_ndarray(format="bgr24")
            video_frame = av.VideoFrame.from_ndarray(frame, format="bgr24")
            video_frame.pts = pts
            video_frame.time_base = time_base

            self.frame_count += 1

            return video_frame

        except Exception as e:
            logger.error(f"Frame decode error: {e}")
            await asyncio.sleep(0.1)
            return await self.recv()


class WebRTCPeer:
    def __init__(self, session_id: str, ws: web.WebSocketResponse):
        self.session_id = session_id
        self.ws = ws
        self.pc: Optional[RTCPeerConnection] = None
        self.video_track: Optional[BrowserVideoTrack] = None
        self.browser_session = None
        self._connected = False
        self._track_added = False
        self._ice_connected = asyncio.Event()

    async def start(self):
        ice_servers = [
            RTCIceServer(
                urls=s["urls"], **({k: v for k, v in s.items() if k != "urls"})
            )
            for s in Config.get_ice_servers()
        ]
        self.pc = RTCPeerConnection(
            configuration=RTCConfiguration(iceServers=ice_servers)
        )

        @self.pc.on("iceconnectionstatechange")
        async def on_ice_connection_state_change():
            if self.pc is None:
                return
            logger.info(f"ICE connection state: {self.pc.iceConnectionState}")
            if self.pc.iceConnectionState == "connected":
                self._connected = True
                self._ice_connected.set()
            elif self.pc.iceConnectionState in ("failed", "closed"):
                self._connected = False

    async def handle_offer(self, data: dict):
        if not self.pc:
            await self.start()

        offer_sdp = data.get("sdp", "")

        await self.pc.setRemoteDescription(
            RTCSessionDescription(sdp=offer_sdp, type="offer")
        )

        if self.video_track and not self._track_added:
            self.pc.addTrack(self.video_track)
            self._track_added = True
            logger.info(f"Track added for session {self.session_id}")

        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)

        await self.ws.send_json({"type": "answer", "sdp": answer.sdp})

    async def handle_ice_candidate(self, data: dict):
        if not self.pc:
            return

        candidate_str = data.get("candidate")
        if candidate_str:
            from aiortc import RTCIceCandidate

            parts = candidate_str.split()
            if len(parts) >= 8:
                ice_candidate = RTCIceCandidate(
                    component=int(parts[1]),
                    foundation=parts[0],
                    ip=parts[4],
                    port=int(parts[5]),
                    priority=int(parts[3]),
                    protocol=parts[2],
                    type=parts[7],
                    sdpMid=data.get("sdpMid"),
                    sdpMLineIndex=data.get("sdpMLineIndex"),
                )
                await self.pc.addIceCandidate(ice_candidate)

    async def start_streaming(self, browser_session):
        self.browser_session = browser_session
        self.video_track = BrowserVideoTrack(browser_session)

        logger.info(f"Streaming prepared for session {self.session_id}")

    async def close(self):
        self._connected = False
        self._track_added = False
        self._ice_connected.clear()
        if self.pc:
            await self.pc.close()
            self.pc = None
        logger.info(f"Peer closed for session {self.session_id}")
