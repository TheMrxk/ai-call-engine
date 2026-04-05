"""
FreeSWITCH ESL 客户端
通过 Event Socket Layer 连接和控制 FreeSWITCH
"""

import socket
import threading
import logging
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum
import re

logger = logging.getLogger(__name__)


class CallState(Enum):
    """通话状态枚举"""
    INITIATED = "initiated"  # 呼叫已发起
    RINGING = "ringing"  # 振铃中
    ANSWERED = "answered"  # 已接通
    IN_CALL = "in_call"  # 通话中
    HANGUP = "hangup"  # 已挂断
    FAILED = "failed"  # 呼叫失败


@dataclass
class CallInfo:
    """通话信息"""
    call_id: str  # FreeSWITCH Call-UUID
    customer_phone: str  # 客户号码
    agent_extension: str  # 坐席分机
    state: CallState  # 通话状态
    start_time: Optional[float] = None  # 开始时间
    end_time: Optional[float] = None  # 结束时间
    duration: int = 0  # 通话时长（秒）
    hangup_cause: str = ""  # 挂断原因


class FreeSWITCHClient:
    """
    FreeSWITCH ESL 客户端

    使用 telnet 协议连接 FreeSWITCH 的 Event Socket Layer，
    实现外拨呼叫、通话控制等功能。
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8021,
        password: str = "ClueCon"
    ):
        self.host = host
        self.port = port
        self.password = password
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.event_handlers: Dict[str, Callable] = {}
        self.event_thread: Optional[threading.Thread] = None
        self.calls: Dict[str, CallInfo] = {}
        self._lock = threading.Lock()

    def connect(self) -> bool:
        """
        连接 FreeSWITCH ESL 服务

        Returns:
            bool: 连接是否成功
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.port))

            # 读取欢迎消息
            welcome = self._read_line()
            logger.info(f"FreeSWITCH 欢迎消息：{welcome}")

            # 认证
            auth_challenge = self._read_line()
            logger.debug(f"认证挑战：{auth_challenge}")

            # 提取挑战值
            match = re.search(r'auth=(\S+)', auth_challenge)
            if match:
                challenge = match.group(1)
                import hashlib
                hash_obj = hashlib.md5(f"{self.password}:{challenge}".encode()).hexdigest()
                auth_cmd = f"auth {hash_obj}\n\n"
                self.socket.sendall(auth_cmd.encode())

                auth_result = self._read_line()
                if "Reply-Text: +OK" in auth_result:
                    self.connected = True
                    logger.info("FreeSWITCH 认证成功")

                    # 启动事件监听线程
                    self._start_event_listener()
                    return True
                else:
                    logger.error(f"认证失败：{auth_result}")
                    return False

            logger.error("认证挑战格式错误")
            return False

        except Exception as e:
            logger.error(f"连接 FreeSWITCH 失败：{e}")
            self.connected = False
            return False

    def disconnect(self):
        """断开 FreeSWITCH 连接"""
        self.connected = False
        if self.event_thread:
            self.event_thread.join(timeout=2)
        if self.socket:
            try:
                self.socket.sendall(b"exit\n\n")
                self.socket.close()
            except:
                pass
            self.socket = None
        logger.info("已断开 FreeSWITCH 连接")

    def _read_line(self) -> str:
        """从 socket 读取一行"""
        data = b""
        while True:
            chunk = self.socket.recv(1)
            if chunk == b"\n":
                break
            data += chunk
        return data.decode("utf-8", errors="ignore")

    def _start_event_listener(self):
        """启动事件监听线程"""
        def listener():
            logger.info("事件监听线程启动")
            while self.connected:
                try:
                    event_name = None
                    event_data = {}

                    # 读取事件内容
                    while True:
                        line = self._read_line().strip()
                        if not line:
                            break
                        if line.startswith("Event-Name:"):
                            event_name = line.split(":", 1)[1].strip()
                        else:
                            key, value = line.split(":", 1) if ":" in line else (line, "")
                            event_data[key.strip()] = value.strip()

                    # 处理事件
                    if event_name and event_name in self.event_handlers:
                        self.event_handlers[event_name](event_data)

                except Exception as e:
                    logger.error(f"事件监听错误：{e}")
                    if self.connected:
                        self.connected = False
                    break

            logger.info("事件监听线程退出")

        self.event_thread = threading.Thread(target=listener, daemon=True)
        self.event_thread.start()

    def register_event_handler(self, event_name: str, handler: Callable):
        """
        注册事件处理器

        Args:
            event_name: 事件名称，如 CHANNEL_CREATE, CHANNEL_ANSWER 等
            handler: 处理函数，接收 event_data 字典参数
        """
        self.event_handlers[event_name] = handler
        logger.info(f"已注册事件处理器：{event_name}")

    def send_command(self, command: str) -> Dict[str, Any]:
        """
        发送命令到 FreeSWITCH

        Args:
            command: 命令字符串

        Returns:
            dict: 命令响应
        """
        if not self.connected or not self.socket:
            raise Exception("未连接到 FreeSWITCH")

        with self._lock:
            self.socket.sendall(f"{command}\n\n".encode())

            response = {}
            while True:
                line = self._read_line().strip()
                if not line:
                    break
                if ":" in line:
                    key, value = line.split(":", 1)
                    response[key.strip()] = value.strip()

            return response

    # ==================== 外拨呼叫功能 ====================

    def originate_call(
        self,
        destination: str,
        caller_id: str = "1000",
        variables: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """
        发起外拨呼叫

        Args:
            destination: 目标号码（客户手机号）
            caller_id: 主叫号码显示
            variables: 通道变量

        Returns:
            str: 通话 UUID，失败返回 None
        """
        # 构建 origination 命令
        cmd_parts = [
            "originate",
            f"{{origination_caller_id_number={caller_id}}}",
            f"sofia/gateway/trunk/{destination}"
        ]

        command = " ".join(cmd_parts)

        try:
            response = self.send_command(command)
            reply_text = response.get("Reply-Text", "")

            if "+OK" in reply_text:
                # 提取 UUID
                match = re.search(r'([0-9a-f-]{36})', reply_text)
                if match:
                    call_uuid = match.group(1)
                    logger.info(f"呼叫发起成功，UUID: {call_uuid}")

                    # 记录通话信息
                    self.calls[call_uuid] = CallInfo(
                        call_id=call_uuid,
                        customer_phone=destination,
                        agent_extension=caller_id,
                        state=CallState.INITIATED
                    )
                    return call_uuid

            logger.error(f"呼叫发起失败：{reply_text}")
            return None

        except Exception as e:
            logger.error(f"发起呼叫异常：{e}")
            return None

    def answer_call(self, channel: str):
        """
        接听来电

        Args:
            channel: 通道名称
        """
        command = f"answer {channel}"
        return self.send_command(command)

    def hangup_call(self, channel: str, cause: str = "NORMAL_CLEARING"):
        """
        挂断电话

        Args:
            channel: 通道名称
            cause: 挂断原因
        """
        command = f"uuid_kill {channel}"
        return self.send_command(command)

    def playback(self, channel: str, file_path: str):
        """
        播放音频文件

        Args:
            channel: 通道名称
            file_path: 音频文件路径
        """
        command = f"playback {file_path} {channel}"
        return self.send_command(command)

    def speak(
        self,
        channel: str,
        text: str,
        voice: str = "say:zh-CN"
    ):
        """
        TTS 语音合成播放

        Args:
            channel: 通道名称
            text: 要播放的文本
            voice: 语音类型
        """
        command = f"speak {voice}:{text} {channel}"
        return self.send_command(command)

    # ==================== 通话管理功能 ====================

    def get_active_calls(self) -> Dict[str, CallInfo]:
        """获取所有活跃通话"""
        return {k: v for k, v in self.calls.items() if v.state not in [CallState.HANGUP, CallState.FAILED]}

    def get_call_info(self, call_id: str) -> Optional[CallInfo]:
        """获取指定通话信息"""
        return self.calls.get(call_id)

    def update_call_state(self, call_id: str, state: CallState):
        """更新通话状态"""
        if call_id in self.calls:
            self.calls[call_id].state = state
            if state == CallState.ANSWERED:
                import time
                self.calls[call_id].start_time = time.time()
            elif state in [CallState.HANGUP, CallState.FAILED]:
                import time
                if self.calls[call_id].start_time:
                    self.calls[call_id].end_time = time.time()
                    self.calls[call_id].duration = int(
                        self.calls[call_id].end_time - self.calls[call_id].start_time
                    )

    # ==================== 内置事件处理器 ====================

    def _setup_default_handlers(self):
        """设置默认的事件处理器"""

        def on_channel_create(event_data):
            call_uuid = event_data.get("Unique-ID", "")
            logger.debug(f"CHANNEL_CREATE: {call_uuid}")
            # 这里可以触发前端通知

        def on_channel_answer(event_data):
            call_uuid = event_data.get("Unique-ID", "")
            logger.info(f"CHANNEL_ANSWER: {call_uuid}")
            self.update_call_state(call_uuid, CallState.ANSWERED)

        def on_channel_hangup(event_data):
            call_uuid = event_data.get("Unique-ID", "")
            cause = event_data.get("Hangup-Cause", "UNKNOWN")
            logger.info(f"CHANNEL_HANGUP: {call_uuid}, cause: {cause}")
            self.update_call_state(call_uuid, CallState.HANGUP)
            if call_uuid in self.calls:
                self.calls[call_uuid].hangup_cause = cause

        def on_channel_bridge(event_data):
            # 桥接事件，表示两路呼叫已经连通
            call_uuid = event_data.get("Unique-ID", "")
            logger.info(f"CHANNEL_BRIDGE: {call_uuid}")
            self.update_call_state(call_uuid, CallState.IN_CALL)

        # 注册默认处理器
        self.register_event_handler("CHANNEL_CREATE", on_channel_create)
        self.register_event_handler("CHANNEL_ANSWER", on_channel_answer)
        self.register_event_handler("CHANNEL_HANGUP", on_channel_hangup)
        self.register_event_handler("CHANNEL_BRIDGE", on_channel_bridge)

        logger.info("默认事件处理器已设置")


# 全局客户端实例
_freeswitch_client: Optional[FreeSWITCHClient] = None


def get_freeswitch_client() -> Optional[FreeSWITCHClient]:
    """获取 FreeSWITCH 客户端单例"""
    global _freeswitch_client
    if _freeswitch_client is None:
        _freeswitch_client = FreeSWITCHClient()
    return _freeswitch_client


def init_freeswitch_client(
    host: str = "freeswitch",
    port: int = 8021,
    password: str = "ClueCon"
) -> FreeSWITCHClient:
    """初始化并连接 FreeSWITCH 客户端"""
    global _freeswitch_client
    _freeswitch_client = FreeSWITCHClient(host, port, password)

    if _freeswitch_client.connect():
        _freeswitch_client._setup_default_handlers()
        logger.info("FreeSWITCH 客户端初始化成功")
        return _freeswitch_client
    else:
        logger.error("FreeSWITCH 客户端连接失败")
        raise ConnectionError("无法连接到 FreeSWITCH")
