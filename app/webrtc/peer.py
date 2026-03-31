import asyncio
import logging
import io
from typing import Optional

import av
from aiohttp import web
from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    RTCConfiguration,
    RTCIceServer,
    VideoStreamTrack,
)
from aiortc.sdp import candidate_from_sdp

from app.browser.manager import BrowserSession
from app.config import Config

logger = logging.getLogger(__name__)


class BrowserVideoTrack(VideoStreamTrack):
    """
    自定义视频轨道：
    - 从 browser_session 持续抓取截图帧（bytes）
    - 用 PyAV 解码图片
    - 转成 aiortc 可发送的 VideoFrame
    """

    def __init__(self, browser_session: BrowserSession):
        super().__init__()
        self.browser_session = browser_session
        self.frame_count = 0

    async def recv(self):
        """
        aiortc 会持续调用 recv() 拉取下一帧。
        这里使用"循环等待"而不是递归，避免长时间无帧时递归堆积。
        """
        target_interval = 1.0 / Config.STREAM_FPS

        while True:
            # 为当前帧生成时间戳
            pts, time_base = await self.next_timestamp()

            logger.debug(f"[VideoTrack] recv() called, frame_count={self.frame_count}")

            # 从 browser_session 获取截图 bytes
            frame_data = await self.browser_session.capture_frame(
                quality=Config.SCREENSHOT_QUALITY
            )

            # 如果当前没拿到图，稍等再继续，不要递归调用自己
            if frame_data is None:
                await asyncio.sleep(target_interval)
                continue

            try:
                # 用 PyAV 从图片 bytes 解码成视频帧
                with av.open(io.BytesIO(frame_data)) as container:
                    # 直接取第一帧（图片通常只有一帧）
                    frame = next(container.decode(video=0))
                    frame_nd = frame.to_ndarray(format="bgr24")

                # 转成 aiortc 可发送的 VideoFrame
                video_frame = av.VideoFrame.from_ndarray(frame_nd, format="bgr24")
                video_frame.pts = pts
                video_frame.time_base = time_base

                self.frame_count += 1
                return video_frame

            except Exception as e:
                logger.exception(f"[VideoTrack] Frame decode error: {e}")
                await asyncio.sleep(target_interval)


class WebRTCPeer:
    """
    单个 WebRTC 会话管理类：
    - 负责创建 RTCPeerConnection
    - 处理 offer / answer
    - 处理 ICE candidate
    - 挂载视频轨道
    - 维护连接状态
    """

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
        """
        初始化 RTCPeerConnection，并注册事件监听。
        """
        # 从配置中读取 ICE（STUN/TURN）服务器
        # Config.get_ice_servers() 期望返回类似：
        # [
        #   {
        #     "urls": [
        #       "turn:107.173.83.242:19303?transport=udp",
        #       "turn:107.173.83.242:19303?transport=tcp"
        #     ],
        #     "username": "admin",
        #     "credential": "hxkj2026"
        #   }
        # ]
        ice_servers = [
            RTCIceServer(
                urls=s["urls"], **({k: v for k, v in s.items() if k != "urls"})
            )
            for s in Config.get_ice_servers()
        ]

        self.pc = RTCPeerConnection(
            configuration=RTCConfiguration(iceServers=ice_servers)
        )

        logger.info(f"[{self.session_id}] RTCPeerConnection created")

        # ===== 关键状态日志：后续排查 WebRTC 问题非常重要 =====

        @self.pc.on("iceconnectionstatechange")
        async def on_ice_connection_state_change():
            if self.pc is None:
                return

            logger.info(
                f"[{self.session_id}] ICE connection state: {self.pc.iceConnectionState}"
            )

            if self.pc.iceConnectionState == "connected":
                self._connected = True
                self._ice_connected.set()
            elif self.pc.iceConnectionState in ("failed", "closed", "disconnected"):
                self._connected = False

        @self.pc.on("connectionstatechange")
        async def on_connection_state_change():
            if self.pc is None:
                return

            logger.info(
                f"[{self.session_id}] PC connection state: {self.pc.connectionState}"
            )

        @self.pc.on("signalingstatechange")
        async def on_signaling_state_change():
            if self.pc is None:
                return

            logger.info(
                f"[{self.session_id}] Signaling state: {self.pc.signalingState}"
            )

        @self.pc.on("icegatheringstatechange")
        async def on_ice_gathering_state_change():
            if self.pc is None:
                return

            logger.info(
                f"[{self.session_id}] ICE gathering state: {self.pc.iceGatheringState}"
            )

    async def _wait_for_ice_gathering_complete(self, timeout: float = 5.0):
        """
        等待 aiortc 收集完本地 ICE candidate。
        这样我们可以把“完整 answer（包含 candidate）”一次性发给前端，
        减少 trickle ICE 的复杂度和时序问题。
        """
        if not self.pc:
            return

        # 最多等待 timeout 秒
        steps = int(timeout * 10)
        for _ in range(steps):
            if self.pc.iceGatheringState == "complete":
                logger.info(f"[{self.session_id}] ICE gathering complete")
                return
            await asyncio.sleep(0.1)

        logger.warning(
            f"[{self.session_id}] ICE gathering timeout, state={self.pc.iceGatheringState}"
        )

    async def handle_offer(self, data: dict):
        """
        处理前端发来的 offer：
        1. setRemoteDescription(offer)
        2. 添加视频轨道
        3. createAnswer()
        4. setLocalDescription(answer)
        5. 等待本地 ICE 收集完成
        6. 把完整 answer 发回前端
        """
        if not self.pc:
            await self.start()

        if not self.pc:
            raise RuntimeError("PeerConnection not initialized")

        offer_sdp = data.get("sdp", "")
        logger.info(f"[{self.session_id}] Received offer, SDP length={len(offer_sdp)}")

        # 设置远端描述（浏览器 offer）
        await self.pc.setRemoteDescription(
            RTCSessionDescription(sdp=offer_sdp, type="offer")
        )

        # 如果视频轨道已准备好且尚未添加，则添加
        if self.video_track and not self._track_added:
            self.pc.addTrack(self.video_track)
            self._track_added = True
            logger.info(f"[{self.session_id}] Video track added")

        # 创建 answer
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)

        # 等待 aiortc 把本地 candidate 收集进 localDescription.sdp
        await self._wait_for_ice_gathering_complete()

        # 注意：必须用 self.pc.localDescription.sdp，而不是 answer.sdp
        # 因为 setLocalDescription 后 localDescription 里才会带上更完整的 candidate
        final_answer_sdp = self.pc.localDescription.sdp
        logger.info(
            f"[{self.session_id}] Sending final answer, SDP length={len(final_answer_sdp)}"
        )

        await self.ws.send_json(
            {
                "type": "answer",
                "sdp": final_answer_sdp,
            }
        )

    async def handle_ice_candidate(self, data: dict):
        """
        处理前端 trickle ICE candidate：
        - 正常 candidate：用 candidate_from_sdp() 解析后 addIceCandidate()
        - candidate = null：表示浏览器 candidate 收集结束，传 None 给 aiortc
        """
        if not self.pc:
            logger.warning(
                f"[{self.session_id}] handle_ice_candidate called before pc init"
            )
            return

        candidate_str = data.get("candidate")

        try:
            # 前端发送 { candidate: null } 表示 candidate 收集结束
            if candidate_str is None:
                await self.pc.addIceCandidate(None)
                logger.info(f"[{self.session_id}] Received end-of-candidates")
                return

            # 用 aiortc 官方解析函数解析浏览器 candidate 字符串
            candidate = candidate_from_sdp(candidate_str)
            candidate.sdpMid = data.get("sdpMid")
            candidate.sdpMLineIndex = data.get("sdpMLineIndex")

            await self.pc.addIceCandidate(candidate)

            logger.info(
                f"[{self.session_id}] Added ICE candidate "
                f"(mid={candidate.sdpMid}, mline={candidate.sdpMLineIndex})"
            )

        except Exception as e:
            logger.exception(
                f"[{self.session_id}] Failed to add ICE candidate: {candidate_str}, error={e}"
            )

    async def start_streaming(self, browser_session):
        """
        在业务层准备好 browser_session 后调用：
        - 保存 browser_session
        - 创建 BrowserVideoTrack
        """
        self.browser_session = browser_session
        self.video_track = BrowserVideoTrack(browser_session)

        logger.info(f"[{self.session_id}] Streaming prepared")

    async def close(self):
        """
        关闭 Peer：
        - 重置状态
        - 关闭 RTCPeerConnection
        """
        self._connected = False
        self._track_added = False
        self._ice_connected.clear()

        if self.pc:
            await self.pc.close()
            self.pc = None

        logger.info(f"[{self.session_id}] Peer closed")
