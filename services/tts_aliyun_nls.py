"""
阿里云智能语音交互 2.0 TTS 客户端
使用阿里云智能语音交互 2.0 API 进行语音合成
文档：https://help.aliyun.com/zh/nls/developer-reference/api-restful

注意：
- 使用的是 AccessToken + Appkey 鉴权方式
- AccessToken 测试用 24h 失效，生产环境需动态生成
"""

import requests
import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class AliyunNlsTTSClient:
    """
    阿里云智能语音交互 2.0 TTS 客户端

    支持音色：
    - zh_female_xiaoyi：知性女声
    - zh_female_xiaoxian：甜美女生
    - zh_male_xiaokang：成熟男声
    - 等更多音色

    完整音色列表：https://help.aliyun.com/zh/nls/developer-reference/tts-voices

    API 文档：https://help.aliyun.com/zh/nls/developer-reference/api-restful
    """

    # 阿里云智能语音交互 2.0 TTS API 端点
    # RESTful API 格式：http://nls-gateway.cn-shanghai.aliyuncs.com/stream/v1/tts
    API_URL = "http://nls-gateway.cn-shanghai.aliyuncs.com/stream/v1/tts"

    # 可用音色列表
    AVAILABLE_VOICES = {
        'zh_female_xiaoyi': '知性女声',
        'zh_female_xiaoxian': '甜美女生',
        'zh_female_xiaomeng': '萌系女生',
        'zh_female_xiaorui': '知性女声（英语）',
        'zh_male_xiaokang': '成熟男声',
        'zh_male_xiaogang': '阳光男声',
        'zh_male_xiaowei': '稳重男声',
        'zh_child_xiaoxiao': '可爱童声',
    }

    def __init__(
        self,
        access_token: str = None,
        appkey: str = None,
        voice: str = 'zh_female_xiaoyi',
        format: str = 'wav',
        sample_rate: int = 16000
    ):
        """
        初始化阿里云智能语音交互 2.0 TTS 客户端

        Args:
            access_token: 阿里云 AccessToken（测试用 24h 失效）
            appkey: 阿里云项目 Appkey
            voice: 默认音色
            format: 输出格式（wav/mp3）
            sample_rate: 采样率（8000/16000/22050/24000/32000/44100/48000）
        """
        self.access_token = access_token or os.getenv('ALIYUN_ACCESS_TOKEN')
        self.appkey = appkey or os.getenv('ALIYUN_APPKEY')
        self.voice = voice
        self.format = format
        self.sample_rate = sample_rate

        if not self.access_token:
            logger.warning("未配置 ALIYUN_ACCESS_TOKEN，TTS 功能将不可用")
        if not self.appkey:
            logger.warning("未配置 ALIYUN_APPKEY")

    def synthesize(
        self,
        text: str,
        output_file: str = None
    ) -> Optional[bytes]:
        """
        语音合成（RESTful API）

        阿里云智能语音交互 2.0 RESTful API 格式：
        GET http://nls-gateway.cn-shanghai.aliyuncs.com/stream/v1/tts?key1=value1&key2=value2
        Headers: X-NLS-Token: <token>

        Args:
            text: 要合成的文本
            output_file: 输出文件路径

        Returns:
            音频数据（bytes），失败返回 None
        """
        if not self.access_token or not self.appkey:
            logger.error("AccessToken 或 Appkey 未配置")
            return None

        # 使用 GET 请求，参数放在 URL 中
        # 这是阿里云 NLS RESTful API 的标准格式
        params = {
            'appkey': self.appkey,
            'text': text,
            'voice': self.voice,
            'format': self.format,
            'sample_rate': str(self.sample_rate),
            'volume': '50',
            'speech_rate': '0',
            'pitch_rate': '0',
        }

        headers = {
            'X-NLS-Token': self.access_token,
        }

        try:
            logger.debug(f"请求参数：{params}")
            logger.debug(f"请求头：{headers}")

            response = requests.get(
                self.API_URL,
                headers=headers,
                params=params,
                timeout=30
            )

            logger.debug(f"响应状态码：{response.status_code}")
            logger.debug(f"响应头：{response.headers}")

            if len(response.content) < 500:
                logger.debug(f"响应内容：{response.content}")

            if response.status_code == 200:
                # 检查响应类型
                content_type = response.headers.get('Content-Type', '')
                logger.debug(f"Content-Type: {content_type}")

                # 如果是音频数据
                if 'audio' in content_type or 'wav' in content_type or 'octet-stream' in content_type or 'application/octet-stream' in content_type:
                    audio_data = response.content
                    logger.info(f"语音合成成功，音频大小：{len(audio_data)} 字节")

                    if output_file:
                        with open(output_file, 'wb') as f:
                            f.write(audio_data)
                        logger.info(f"音频已保存到：{output_file}")

                    return audio_data
                else:
                    # 尝试直接保存内容，可能是音频但没有正确的 Content-Type
                    if len(response.content) > 100:  # 音频数据通常较大
                        logger.warning(f"响应 Content-Type 为 {content_type}，但数据大小 {len(response.content)} 字节，可能是音频")
                        audio_data = response.content

                        if output_file:
                            with open(output_file, 'wb') as f:
                                f.write(audio_data)
                            logger.info(f"音频已保存到：{output_file}")

                        return audio_data

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
_tts_client: Optional[AliyunNlsTTSClient] = None


def get_aliyun_nls_tts_client() -> Optional[AliyunNlsTTSClient]:
    """获取阿里云智能语音交互 2.0 TTS 客户端单例"""
    global _tts_client
    return _tts_client


def init_aliyun_nls_tts_client(
    access_token: str = None,
    appkey: str = None,
    voice: str = 'zh_female_xiaoyi',
    format: str = 'wav',
    sample_rate: int = 16000
) -> AliyunNlsTTSClient:
    """初始化阿里云智能语音交互 2.0 TTS 客户端"""
    global _tts_client

    _tts_client = AliyunNlsTTSClient(
        access_token=access_token,
        appkey=appkey,
        voice=voice,
        format=format,
        sample_rate=sample_rate
    )

    logger.info(f"阿里云 NLS TTS 客户端已初始化，音色：{voice}, 格式：{format}@{sample_rate}Hz")
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
    client = get_aliyun_nls_tts_client()

    if not client:
        # 尝试初始化
        access_token = os.getenv('ALIYUN_ACCESS_TOKEN')
        appkey = os.getenv('ALIYUN_APPKEY')
        if access_token and appkey:
            client = init_aliyun_nls_tts_client(
                access_token=access_token,
                appkey=appkey,
                voice=voice or 'zh_female_xiaoyi'
            )
        else:
            logger.error("未配置 ALIYUN_ACCESS_TOKEN 或 ALIYUN_APPKEY")
            return None

    if voice:
        client.set_voice(voice)

    return client.synthesize(text, output_file)
