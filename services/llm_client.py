"""
LLM 对话引擎
支持 DeepSeek、通义千问等 OpenAI 兼容格式的大模型 API
"""

import requests
import json
import logging
from typing import Optional, List, Dict, Generator


class LLMClient:
    """大模型对话客户端"""

    # 支持的提供商配置
    PROVIDERS = {
        'deepseek': {
            'api_url': 'https://api.deepseek.com/chat/completions',
            'auth_header': 'Authorization',
            'auth_prefix': 'Bearer '
        },
        'dashscope': {
            'api_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
            'auth_header': 'Authorization',
            'auth_prefix': 'Bearer '
        },
        'dashscope_coding': {
            'api_url': 'https://coding.dashscope.aliyuncs.com/v1/chat/completions',
            'auth_header': 'Authorization',
            'auth_prefix': 'Bearer '
        },
        'dashscope_anthropic': {
            'api_url': 'https://coding.dashscope.aliyuncs.com/apps/anthropic/v1/messages',
            'auth_header': 'x-api-key',
            'auth_prefix': '',
            'format': 'anthropic'  # 使用 Anthropic 格式
        },
        'openai': {
            'api_url': 'https://api.openai.com/v1/chat/completions',
            'auth_header': 'Authorization',
            'auth_prefix': 'Bearer '
        }
    }

    def __init__(
        self,
        api_key: str,
        provider: str = 'deepseek',
        model: str = None,
        api_url: str = None
    ):
        """
        初始化 LLM 客户端

        Args:
            api_key: API 密钥
            provider: 服务商名称 (deepseek/dashscope/openai)
            model: 模型名称
            api_url: 自定义 API 地址
        """
        self.api_key = api_key
        self.provider = provider
        self.api_url = api_url or self.PROVIDERS.get(provider, {}).get('api_url', '')

        # 默认模型
        if model:
            self.model = model
        elif provider == 'deepseek':
            self.model = 'deepseek-chat'
        elif provider == 'dashscope':
            self.model = 'qwen-plus'
        elif provider == 'dashscope_coding':
            self.model = 'qwen3-coder-next'  # Coding Plan 支持，速度更快
        elif provider == 'dashscope_anthropic':
            self.model = 'claude-3-5-sonnet-20240620'  # Anthropic 兼容协议
        else:
            self.model = 'gpt-3.5-turbo'

    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Optional[str]:
        """
        发送对话请求

        Args:
            messages: 对话历史列表
            system_prompt: 系统提示词
            temperature: 温度参数 (0-2)
            max_tokens: 最大输出 token 数

        Returns:
            AI 回复内容，失败返回 None
        """
        import logging
        logger = logging.getLogger(__name__)

        if not self.api_key:
            logger.error("[LLM] Error: API Key not configured")
            return None

        logger.info(f"[LLM] 请求：provider={self.provider}, api_url={self.api_url}, model={self.model}")
        logger.info(f"[LLM] 消息：{messages}")

        # 检查是否使用 Anthropic 格式
        use_anthropic = self.PROVIDERS.get(self.provider, {}).get('format') == 'anthropic'

        # 构建消息列表
        if system_prompt:
            if use_anthropic:
                # Anthropic 格式：system 参数单独传
                pass
            else:
                messages = [{'role': 'system', 'content': system_prompt}] + messages

        if use_anthropic:
            # Anthropic Message API 格式
            payload = {
                'model': self.model,
                'messages': messages,
                'max_tokens': max_tokens,
                'system': system_prompt or '你是一个有帮助的助手。'
            }
        else:
            # OpenAI 兼容格式
            payload = {
                'model': self.model,
                'messages': messages,
                'temperature': temperature,
                'max_tokens': max_tokens
            }

        headers = {
            'Content-Type': 'application/json',
            self.PROVIDERS.get(self.provider, {}).get('auth_header', 'Authorization'):
                self.PROVIDERS.get(self.provider, {}).get('auth_prefix', '') + self.api_key
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            logger.info(f"[LLM] 响应状态码：{response.status_code}")

            if response.status_code == 200:
                result = response.json()
                logger.info(f"[LLM] 响应结果：{result}")

                if use_anthropic:
                    # Anthropic 格式解析
                    content = result.get('content', [{}])[0].get('text', '')
                else:
                    # OpenAI 格式解析
                    content = result.get('choices', [{}])[0].get('message', {}).get('content', '')

                logger.info(f"[LLM] 提取内容：{content}")
                return content.strip() if content else None
            else:
                logger.error(f"[LLM] Error {response.status_code}: {response.text}")
                return None

        except Exception as e:
            logger.error(f"[LLM] Request failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def chat_streaming(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Generator[str, None, None]:
        """
        流式对话（边生成边返回）

        Args:
            messages: 对话历史列表
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大输出 token 数

        Yields:
            AI 回复的内容片段
        """
        if not self.api_key:
            print("[LLM] Error: API Key not configured")
            return

        if system_prompt:
            messages = [{'role': 'system', 'content': system_prompt}] + messages

        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'stream': True  # 启用流式
        }

        headers = {
            'Content-Type': 'application/json',
            self.PROVIDERS.get(self.provider, {}).get('auth_header', 'Authorization'):
                self.PROVIDERS.get(self.provider, {}).get('auth_prefix', '') + self.api_key
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60,
                stream=True
            )

            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        # 解析 SSE 格式
                        if line.startswith('data: '):
                            data = line[6:]
                            if data != '[DONE]':
                                try:
                                    chunk = json.loads(data)
                                    delta = chunk.get('choices', [{}])[0].get('delta', {}).get('content', '')
                                    if delta:
                                        yield delta
                                except json.JSONDecodeError:
                                    pass
            else:
                print(f"[LLM] Error {response.status_code}: {response.text}")

        except Exception as e:
            print(f"[LLM] Streaming failed: {e}")


# 银行营销场景默认提示词
DEFAULT_BANK_SYSTEM_PROMPT = """你是一个专业的银行 AI 客服代表，正在进行电话营销外呼。

你的任务是：
1. 向客户介绍银行的优惠活动或理财产品
2. 耐心解答客户的疑问
3. 引导客户办理业务

要求：
- 语气友好、专业、有亲和力
- 回复简洁，每次不超过 50 字（因为是电话语音）
- 不要强行推销，尊重客户意愿
- 如果客户明确表示不需要，礼貌结束通话"""


# 全局客户端实例
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> Optional[LLMClient]:
    """获取 LLM 客户端单例"""
    global _llm_client
    return _llm_client


def init_llm_client(
    provider: str = 'deepseek',
    api_key: str = None,
    model: str = None,
    api_url: str = None
) -> LLMClient:
    """初始化 LLM 客户端"""
    global _llm_client
    _llm_client = LLMClient(api_key=api_key, provider=provider, model=model, api_url=api_url)
    logger = logging.getLogger(__name__)
    logger.info(f"LLM 客户端已初始化，提供商：{provider}")
    return _llm_client


# 便捷函数
def create_llm_client(
    api_key: str,
    provider: str = 'deepseek'
) -> LLMClient:
    """创建 LLM 客户端"""
    return LLMClient(api_key, provider)


def chat_with_llm(
    user_message: str,
    api_key: str,
    provider: str = 'deepseek',
    system_prompt: str = None,
    conversation_history: List[Dict] = None
) -> Optional[str]:
    """
    与大模型对话的便捷函数

    Args:
        user_message: 用户消息
        api_key: API 密钥
        provider: 服务商
        system_prompt: 系统提示词
        conversation_history: 对话历史

    Returns:
        AI 回复内容
    """
    client = create_llm_client(api_key, provider)

    messages = conversation_history or []
    messages.append({'role': 'user', 'content': user_message})

    return client.chat(
        messages=messages,
        system_prompt=system_prompt or DEFAULT_BANK_SYSTEM_PROMPT
    )


if __name__ == '__main__':
    import os

    # 测试
    api_key = os.environ.get('LLM_API_KEY', '')

    if not api_key:
        print("请设置 LLM_API_KEY 环境变量")
        exit(1)

    print("测试 LLM 对话...")
    print(f"Provider: deepseek")

    client = LLMClient(api_key, provider='deepseek')

    # 测试对话
    response = client.chat(
        messages=[{'role': 'user', 'content': '你好，请介绍一下你自己'}],
        system_prompt=DEFAULT_BANK_SYSTEM_PROMPT
    )

    if response:
        print(f"\nAI 回复:\n{response}")
    else:
        print("对话失败，请检查 API Key 配置")
