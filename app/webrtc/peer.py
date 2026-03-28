import asyncio
import json
import logging
import av
import numpy as np
from typing import Optional
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaBlackhole

logger = logging.getLogger(__name__)


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
            img = av.Image.from_bytes(
                frame_data,
                format='jpeg'
            )
            
            frame = img.to_ndarray(format='bgr24')
            video_frame = av.VideoFrame.from_ndarray(frame, format='bgr24')
            video_frame.pts = pts
            video_frame.time_base = time_base
            
            self.frame_count += 1
            
            return video_frame
            
        except Exception as e:
            logger.error(f'Frame decode error: {e}')
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

    async def start(self):
        self.pc = RTCPeerConnection()
        
        @self.pc.on('iceconnectionstatechange')
        async def on_ice_connection_state_change():
            logger.info(f'ICE connection state: {self.pc.iceConnectionState}')
            if self.pc.iceConnectionState == 'connected':
                self._connected = True
            elif self.pc.iceConnectionState in ('failed', 'closed'):
                self._connected = False

    async def handle_offer(self, data: dict):
        if not self.pc:
            await self.start()
        
        await self.pc.setRemoteDescription(RTCSessionDescription(
            sdp=data.get('sdp'),
            type='offer'
        ))
        
        if not self.video_track and self.browser_session:
            self.video_track = BrowserVideoTrack(self.browser_session)
            self.pc.addTrack(self.video_track)
        
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)
        
        await self.ws.send_json({
            'type': 'answer',
            'sdp': answer.sdp
        })
        
    async def handle_ice_candidate(self, data: dict):
        if not self.pc:
            return
        
        candidate = data.get('candidate')
        if candidate:
            from aiortc import RTCIceCandidate
            ice_candidate = RTCIceCandidate(
                sdpMid=data.get('sdpMid'),
                sdpMLineIndex=data.get('sdpMLineIndex'),
                candidate=candidate
            )
            await self.pc.addIceCandidate(ice_candidate)

    async def start_streaming(self, browser_session):
        self.browser_session = browser_session
        
        self.video_track = BrowserVideoTrack(browser_session)
        self.pc.addTrack(self.video_track)
        
        logger.info(f'Started streaming for session {self.session_id}')

    async def close(self):
        self._connected = False
        if self.pc:
            await self.pc.close()
            self.pc = None
        logger.info(f'Peer closed for session {self.session_id}')
