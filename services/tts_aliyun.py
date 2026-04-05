"""
阿里云 TTS 客户端 (Aliyun DashScope TTS)
使用阿里云百炼 DashScope API 进行语音合成
文档：https://help.aliyun.com/zh/dashscope/developer-reference/tts-api

注意：需要在 .env 中配置 DASHSCOPE_API_KEY
"""

import requests
import json
import logging
import os
from typing import Optional
import uuid

logger = logging.getLogger(__name__)


class AliyunTTSClient:
    """
    阿里云 DashScope TTS 客户端

    支持音色：
    - longhua: 龙华（知性女声）
    - longanyang: 龙小阳（阳光男声）
    - jiajia: 佳佳（亲切女声）
    - siqi: 思琪（温柔女声）
    等更多音色

    完整音色列表：https://help.aliyun.com/zh/model-studio/non-realtime-cosyvoice-api
    """

    # 阿里云 TTS API 端点 - CosyVoice 正确格式
    API_URL = "https://dashscope.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer"

    # 可用模型
    AVAILABLE_MODELS = {
        'cosyvoice-v3-flash': 'CosyVoice v3 Flash（最新快速版）',
        'cosyvoice-v2': 'CosyVoice v2',
        'cosyvoice-v1': 'CosyVoice v1',
    }

    # 可用音色列表
    AVAILABLE_VOICES = {
        'longhua': '龙华（知性女声）',
        'longanyang': '龙小阳（阳光男声）',
        'longxiaocheng': '龙小城（成熟男声）',
        'longxiaobei': '龙小北（温暖男声）',
        'longmeiqi': '龙美琪（甜美女声）',
        'longyaoya': '龙娅娅（活泼女声）',
    }

    def __init__(
        self,
        api_key: str = None,
        voice: str = 'longhua',
        model: str = 'cosyvoice-v3-flash'
    ):
        """
        初始化阿里云 TTS 客户端

        Args:
            api_key: 阿里云 DashScope API Key
            voice: 默认音色
            model: TTS 模型
        """
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY')
        self.voice = voice
        self.model = model

        if not self.api_key:
            logger.warning("未配置 DASHSCOPE_API_KEY，TTS 功能将不可用")

        # 请求头
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'X-DashScope-DataInspection': 'enable'
        }

    def synthesize(
        self,
        text: str,
        output_file: str = None
    ) -> Optional[bytes]:
        """
        语音合成 - CosyVoice API 格式

        Args:
            text: 要合成的文本
            output_file: 输出文件路径

        Returns:
            音频数据（bytes），失败返回 None
        """
        if not self.api_key:
            logger.error("API Key 未配置")
            return None

        # CosyVoice API 格式
        # https://help.aliyun.com/zh/model-studio/non-realtime-cosyvoice-api
        payload = {
            "model": self.model,
            "input": {
                "text": text,
                "voice": self.voice,
                "format": "wav"
            },
            "parameters": {
                "volume": 50,
                "rate": 1.0,
                "pitch": 1.0
            }
        }

        try:
            logger.info(f"请求 TTS: model={self.model}, voice={self.voice}, text={text[:50]}...")

            response = requests.post(
                self.API_URL,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            logger.debug(f"响应状态码：{response.status_code}")
            logger.debug(f"响应头：{response.headers}")

            if response.status_code == 200:
                # 检查响应类型
                content_type = response.headers.get('Content-Type', '')

                # 如果是音频数据
                if 'audio' in content_type or 'wav' in content_type or 'octet-stream' in content_type or 'application/octet-stream' in content_type:
                    audio_data = response.content
                    logger.info(f"语音合成成功，音频大小：{len(audio_data)} 字节")

                    if output_file:
                        with open(output_file, 'wb') as f:
                            f.write(audio_data)
                        logger.info(f"音频已保存到：{output_file}")

                    return audio_data

                # 如果是 JSON 响应（可能是流式或 Base64）
                elif 'application/json' in content_type:
                    try:
                        result = response.json()

                        # 检查是否有 audio 字段（Base64）
                        if 'output' in result and 'audio' in result.get('output', {}):
                            audio_base64 = result['output']['audio']
                            import base64
                            audio_data = base64.b64decode(audio_base64)
                            logger.info(f"语音合成成功（Base64），音频大小：{len(audio_data)} 字节")

                            if output_file:
                                with open(output_file, 'wb') as f:
                                    f.write(audio_data)

                            return audio_data

                        # 检查错误
                        if 'code' in result:
                            logger.error(f"API 错误：{result.get('code')} - {result.get('message', '')}")
                            return None

                        logger.debug(f"JSON 响应：{result}")

                    except json.JSONDecodeError as e:
                        logger.error(f"JSON 解析失败：{e}")
                        return None

                logger.error(f"未知响应类型：{content_type}")
                return None

            else:
                # HTTP 错误
                try:
                    error_data = response.json()
                    logger.error(f"HTTP {response.status_code}: {error_data}")
                except:
                    logger.error(f"HTTP {response.status_code}: {response.text[:500]}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败：{e}")
            return None
        except Exception as e:
            logger.error(f"未知错误：{e}")
            return None

    def get_available_voices(self) -> dict:
        """获取可用音色列表"""
        return self.AVAILABLE_VOICES

    def set_voice(self, voice: str):
        """设置音色"""
        if voice in self.AVAILABLE_VOICES:
            self.voice = voice
            logger.info(f"音色已设置为：{voice}")
        else:
            logger.warning(f"音色 {voice} 不存在，使用默认音色 {self.voice}")


# 全局客户端实例
_tts_client: Optional[AliyunTTSClient] = None


def get_aliyun_tts_client() -> Optional[AliyunTTSClient]:
    """获取阿里云 TTS 客户端单例"""
    global _tts_client
    return _tts_client


def init_aliyun_tts_client(
    api_key: str = None,
    voice: str = 'jiajia',
    model: str = 'sambert-zh-v1'
) -> AliyunTTSClient:
    """初始化阿里云 TTS 客户端"""
    global _tts_client

    _tts_client = AliyunTTSClient(
        api_key=api_key,
        voice=voice,
        model=model
    )

    logger.info(f"阿里云 TTS 客户端已初始化，音色：{voice}, 模型：{model}")
    return _tts_client


def synthesize_speech(
    text: str,
    output_file: str = None,
    voice: str = None
) -> Optional[bytes]:
    """
    便捷函数：语音合成

    Args:
        text: 要合成的文本
        output_file: 输出文件路径
        voice: 音色（可选，使用默认音色）

    Returns:
        音频数据
    """
    client = get_aliyun_tts_client()

    if not client:
        # 尝试初始化
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if api_key:
            client = init_aliyun_tts_client(api_key=api_key, voice=voice or 'jiajia')
        else:
            logger.error("未配置 DASHSCOPE_API_KEY")
            return None

    if voice:
        client.set_voice(voice)

    return client.synthesize(text, output_file)
