"""
TTS 工厂模块
支持切换不同的 TTS 服务提供商

支持的提供商：
- aliyun: 阿里云 DashScope TTS（推荐）
- doubao: 火山引擎豆包 TTS（HTTP API 方式）
"""

import logging
from typing import Optional, Any
from .tts_aliyun import AliyunTTSClient, init_aliyun_tts_client, get_aliyun_tts_client
from .tts_client import DoubaoRealtimeClient, init_tts_client, get_tts_client

logger = logging.getLogger(__name__)


class TTSFactory:
    """TTS 工厂类"""

    _instance = None
    _provider = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TTSFactory, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls):
        """获取工厂单例"""
        return cls()

    @classmethod
    def initialize(
        cls,
        provider: str = 'aliyun',
        **kwargs
    ) -> Any:
        """
        初始化 TTS 客户端

        Args:
            provider: TTS 提供商 ('aliyun' 或 'doubao')
            **kwargs: 传递给具体提供商的参数

        Returns:
            初始化后的 TTS 客户端
        """
        cls._provider = provider

        if provider == 'aliyun':
            api_key = kwargs.get('api_key')
            voice = kwargs.get('voice', 'jiajia')
            model = kwargs.get('model', 'sambert-zh-v1')

            cls._client = init_aliyun_tts_client(
                api_key=api_key,
                voice=voice,
                model=model
            )
            logger.info(f"TTS 工厂已初始化：提供商=aliyun, 音色={voice}")

        elif provider == 'doubao':
            appid = kwargs.get('appid')
            access_token = kwargs.get('access_token')
            voice = kwargs.get('voice', 'zh_female_vv_jupiter_bigtts')
            secret_key = kwargs.get('secret_key')

            cls._client = init_tts_client(
                provider='doubao',
                appid=appid,
                access_token=access_token,
                voice=voice,
                secret_key=secret_key
            )
            logger.info(f"TTS 工厂已初始化：提供商=doubao, 音色={voice}")

        else:
            raise ValueError(f"不支持的 TTS 提供商：{provider}")

        return cls._client

    @classmethod
    def get_client(cls) -> Optional[Any]:
        """获取当前 TTS 客户端"""
        if cls._client is None:
            # 尝试默认初始化
            from dotenv import load_dotenv
            import os
            load_dotenv()

            # 默认使用阿里云
            api_key = os.getenv('DASHSCOPE_API_KEY')
            if api_key:
                return cls.initialize(provider='aliyun', api_key=api_key)
            else:
                # 尝试豆包
                appid = os.getenv('DOUBAO_APPID')
                access_token = os.getenv('DOUBAO_ACCESS_TOKEN')
                if appid and access_token:
                    return cls.initialize(
                        provider='doubao',
                        appid=appid,
                        access_token=access_token,
                        secret_key=os.getenv('DOUBAO_SECRET_KEY')
                    )

        return cls._client

    @classmethod
    def get_provider(cls) -> Optional[str]:
        """获取当前提供商"""
        return cls._provider

    @classmethod
    def switch_provider(cls, provider: str, **kwargs) -> Any:
        """
        切换 TTS 提供商

        Args:
            provider: 新的提供商
            **kwargs: 传递给新提供商的参数

        Returns:
            新的客户端实例
        """
        logger.info(f"切换 TTS 提供商：{cls._provider} -> {provider}")
        return cls.initialize(provider=provider, **kwargs)

    @classmethod
    def synthesize(
        cls,
        text: str,
        output_file: str = None,
        voice: str = None
    ) -> Optional[bytes]:
        """
        语音合成（便捷方法）

        Args:
            text: 要合成的文本
            output_file: 输出文件路径
            voice: 音色（可选）

        Returns:
            音频数据
        """
        client = cls.get_client()

        if client is None:
            logger.error("TTS 客户端未初始化")
            return None

        # 根据客户端类型调用相应方法
        if isinstance(client, AliyunTTSClient):
            if voice:
                client.set_voice(voice)
            return client.synthesize(text, output_file)

        elif isinstance(client, DoubaoRealtimeClient):
            if voice:
                client.voice = voice
            return client.synthesize(text, output_file)

        else:
            logger.error(f"未知的客户端类型：{type(client)}")
            return None


# 便捷函数
def init_tts(provider: str = 'aliyun', **kwargs):
    """初始化 TTS"""
    return TTSFactory.initialize(provider=provider, **kwargs)


def get_tts():
    """获取 TTS 客户端"""
    return TTSFactory.get_client()


def switch_tts(provider: str, **kwargs):
    """切换 TTS 提供商"""
    return TTSFactory.switch_provider(provider=provider, **kwargs)


def synthesize_speech(text: str, output_file: str = None, voice: str = None):
    """语音合成"""
    return TTSFactory.synthesize(text=text, output_file=output_file, voice=voice)
