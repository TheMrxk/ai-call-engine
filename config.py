#!/usr/bin/env python3
"""
AI Call Engine - 配置管理工具

用途:
1. 配置向导（交互式）
2. 命令行配置
3. 配置验证
4. 豆包配置指南

使用:
    python config.py              # 交互式配置向导
    python config.py show         # 查看当前配置
    python config.py set KEY VAL  # 设置配置项
    python config.py test         # 测试连接
    python config.py doubao       # 豆包配置指南
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import Optional, Dict

# 配置文件路径
CONFIG_FILE = Path(".env")
CONFIG_TEMPLATE = Path(".env.example")

# 配置项说明
CONFIG_DESCRIPTIONS = {
    # LLM 配置
    "LLM_API_KEY": {
        "desc": "阿里云百炼 API Key",
        "required": True,
        "example": "sk-sp-xxxxxxxxxxxxxxxx",
        "url": "https://dashscope.console.aliyun.com/apiKey"
    },
    "LLM_PROVIDER": {
        "desc": "LLM 提供商",
        "required": False,
        "default": "dashscope_coding",
        "options": ["dashscope_coding", "dashscope", "deepseek", "openai"]
    },
    "LLM_MODEL": {
        "desc": "LLM 模型名称",
        "required": False,
        "default": "qwen3-coder-next",
        "options": ["qwen3-coder-next", "qwen-plus", "qwen-turbo", "deepseek-chat"]
    },

    # TTS 配置
    "TTS_PROVIDER": {
        "desc": "TTS 提供商",
        "required": False,
        "default": "doubao",
        "options": ["doubao", "aliyun"]
    },
    "DOUBAO_APPID": {
        "desc": "火山引擎豆包 APPID",
        "required": False,
        "default": "2058216235"
    },
    "DOUBAO_ACCESS_TOKEN": {
        "desc": "火山引擎豆包 Access Token",
        "required": True,
        "example": "HthevSMrUFC7z8Nxfb0yKFyR1XVNeW-W",
        "url": "https://console.volcengine.com/speech/service"
    },
    "DOUBAO_SPEAKER": {
        "desc": "豆包 TTS 音色",
        "required": False,
        "default": "zh_female_vv_uranus_bigtts",
        "note": "vivi 2.0 音色"
    },

    # ASR 配置
    "ASR_PROVIDER": {
        "desc": "ASR 提供商",
        "required": False,
        "default": "volcengine_doubao",
        "options": ["volcengine_doubao", "funasr"]
    },
    "DOUBAO_ASR_RESOURCE_ID": {
        "desc": "豆包 ASR 资源 ID",
        "required": False,
        "default": "volc.seedasr.sauc.duration",
        "note": "小时版计费"
    },
    "DOUBAO_ASR_WS_URL": {
        "desc": "豆包 ASR WebSocket 地址",
        "required": False,
        "default": "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_async"
    },

    # 服务配置
    "PORT": {
        "desc": "服务端口",
        "required": False,
        "default": "5001"
    },
    "HOST": {
        "desc": "服务地址",
        "required": False,
        "default": "0.0.0.0"
    }
}


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_file: Path = CONFIG_FILE):
        self.config_file = config_file
        self.config: Dict[str, str] = {}
        self.load()

    def load(self):
        """加载配置"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        self.config[key.strip()] = value.strip().strip('"\'')

    def save(self):
        """保存配置"""
        # 读取模板文件
        template_lines = []
        if CONFIG_TEMPLATE.exists():
            with open(CONFIG_TEMPLATE, 'r', encoding='utf-8') as f:
                template_lines = f.readlines()
        else:
            # 如果没有模板，生成基本结构
            template_lines = [
                "# AI Call Engine Configuration\n",
                "\n",
                "# LLM Configuration\n",
                "\n",
                "# TTS Configuration\n",
                "\n",
                "# ASR Configuration\n",
                "\n",
                "# Service Configuration\n",
            ]

        # 写入配置
        with open(self.config_file, 'w', encoding='utf-8') as f:
            for line in template_lines:
                f.write(line)
                # 在每节后添加配置
                if line.startswith('# LLM'):
                    for k, v in self.config.items():
                        if k.startswith('LLM'):
                            f.write(f"{k}={v}\n")
                elif line.startswith('# TTS'):
                    for k, v in self.config.items():
                        if k.startswith('DOUBAO') or k.startswith('TTS'):
                            f.write(f"{k}={v}\n")
                elif line.startswith('# ASR'):
                    for k, v in self.config.items():
                        if 'ASR' in k:
                            f.write(f"{k}={v}\n")
                elif line.startswith('# Service'):
                    for k, v in self.config.items():
                        if k in ['PORT', 'HOST']:
                            f.write(f"{k}={v}\n")

    def get(self, key: str, default: str = None) -> Optional[str]:
        """获取配置值"""
        return self.config.get(key, default)

    def set(self, key: str, value: str):
        """设置配置值"""
        self.config[key] = value
        self.save()

    def show(self):
        """显示当前配置"""
        print("\n" + "=" * 60)
        print("  AI Call Engine - 当前配置")
        print("=" * 60)

        for key, desc in CONFIG_DESCRIPTIONS.items():
            value = self.config.get(key, desc.get('default', ''))
            is_set = key in self.config

            # 隐藏敏感信息
            if 'KEY' in key or 'TOKEN' in key or 'SECRET' in key:
                display_value = f"{'*' * 8}{value[-4:]}" if value else "(未设置)"
            else:
                display_value = value if value else "(未设置)"

            # 标记状态
            status = "✓" if is_set else "○"
            if desc.get('required') and not value:
                status = "✗"

            print(f"\n[{status}] {key}")
            print(f"    说明：{desc['desc']}")
            print(f"    当前值：{display_value}")

            if desc.get('options'):
                print(f"    可选值：{', '.join(desc['options'])}")
            if desc.get('url'):
                print(f"    申请地址：{desc['url']}")

        print("\n" + "=" * 60)

    def test_connection(self):
        """测试服务连接"""
        print("\n正在测试服务连接...")

        # 测试健康检查
        try:
            resp = requests.get(f"http://localhost:{self.config.get('PORT', '5001')}/api/health", timeout=5)
            if resp.status_code == 200:
                print("✓ 服务健康检查通过")
            else:
                print(f"✗ 服务健康检查失败：{resp.status_code}")
        except Exception as e:
            print(f"✗ 无法连接到服务：{e}")
            print("  请确保服务已启动：docker-compose up -d")

        # 测试 LLM 配置
        llm_key = self.config.get('LLM_API_KEY')
        if llm_key:
            print("✓ LLM API Key 已配置")
            # 可以在这里添加实际的 API 测试
        else:
            print("✗ LLM API Key 未配置")

        # 测试 TTS 配置
        doubao_token = self.config.get('DOUBAO_ACCESS_TOKEN')
        if doubao_token:
            print("✓ 豆包 Access Token 已配置")
        else:
            print("✗ 豆包 Access Token 未配置")

    def doubao_guide(self):
        """豆包配置指南"""
        print("\n" + "=" * 60)
        print("  火山引擎豆包配置指南")
        print("=" * 60)

        print("""
【步骤 1】访问火山引擎控制台

    https://console.volcengine.com/speech/service

【步骤 2】登录/注册账号

    - 如果没有账号，先注册火山引擎账号
    - 完成实名认证（需要用于 API 调用）

【步骤 3】创建应用

    1. 在左侧菜单选择「语音合成」或「语音识别」
    2. 点击「创建应用」
    3. 填写应用名称（例如：ai-call-engine）
    4. 选择实例：
       - TTS: seed-tts-2.0 (语音合成模型 2.0)
       - ASR: seed-asr-2.0 (语音识别模型 2.0)
    5. 点击「创建」

【步骤 4】获取 Access Token

    1. 进入应用详情页
    2. 找到「鉴权信息」或「Access Token」
    3. 复制 Access Token
    4. 运行命令配置：

       python config.py set DOUBAO_ACCESS_TOKEN "你的 Access Token"

【步骤 5】配置 APPID（可选）

    在应用详情页找到 APPID，然后运行：

       python config.py set DOUBAO_APPID "你的 APPID"

【步骤 6】验证配置

    python config.py test

【费用说明】

    - ASR: ¥0.002/次（5 秒以内）
    - TTS: ¥0.001/次（30 字以内）
    - 新用户有免费额度

【常见问题】

    Q: Access Token 多久过期？
    A: 长期有效，除非手动重置

    Q: 免费额度有多少？
    A: 新用户注册后有一定免费测试额度

    Q: 如何充值？
    A: 在火山引擎控制台 → 费用中心 → 充值

""")
        print("=" * 60)


def interactive_wizard(config: ConfigManager):
    """交互式配置向导"""
    print("\n" + "=" * 60)
    print("  AI Call Engine - 配置向导")
    print("=" * 60)
    print("""
欢迎使用 AI Call Engine 配置向导！

本向导将帮助您配置必要的 API Key 和参数。
已设置的配置项会显示当前值，直接回车可跳过修改。

""")

    # 必要的配置
    required_keys = [k for k, v in CONFIG_DESCRIPTIONS.items() if v.get('required')]

    for key in required_keys:
        desc = CONFIG_DESCRIPTIONS[key]
        current = config.get(key, '')

        print(f"\n【{key}】")
        print(f"说明：{desc['desc']}")

        if current:
            display = f"{'*' * 8}{current[-4:]}"
            print(f"当前值：{display}")

        if desc.get('url'):
            print(f"申请地址：{desc['url']}")

        value = input(f"请输入{'新的' if current else ''}值（回车跳过）: ")

        if value:
            config.set(key, value)
            print(f"✓ 已设置 {key}")

    print("\n" + "=" * 60)
    print("  配置完成！")
    print("=" * 60)
    print("""
下一步:
1. 运行 'python config.py show' 查看完整配置
2. 运行 'python config.py test' 测试连接
3. 启动服务：docker-compose up -d
""")


def main():
    config = ConfigManager()

    if len(sys.argv) < 2:
        # 交互式配置向导
        interactive_wizard(config)
        return

    command = sys.argv[1]

    if command == "show":
        config.show()

    elif command == "set":
        if len(sys.argv) < 4:
            print("用法：python config.py set KEY VALUE")
            print("示例：python config.py set LLM_API_KEY sk-sp-xxxxx")
            sys.exit(1)
        key = sys.argv[2]
        value = sys.argv[3]
        config.set(key, value)
        print(f"✓ 已设置 {key}={value}")

    elif command == "test":
        config.test_connection()

    elif command == "doubao" or command == "config_doubao":
        config.doubao_guide()

    elif command == "help" or command == "-h":
        print("""
AI Call Engine - 配置管理工具

用法:
    python config.py              # 交互式配置向导
    python config.py show         # 查看当前配置
    python config.py set KEY VAL  # 设置配置项
    python config.py test         # 测试连接
    python config.py doubao       # 豆包配置指南

示例:
    # 设置 LLM API Key
    python config.py set LLM_API_KEY "sk-sp-xxxxxxxx"

    # 设置豆包 Access Token
    python config.py set DOUBAO_ACCESS_TOKEN "xxxxxxxx"

    # 查看配置
    python config.py show

    # 测试连接
    python config.py test
""")

    else:
        print(f"未知命令：{command}")
        print("运行 'python config.py help' 查看帮助")
        sys.exit(1)


if __name__ == '__main__':
    main()
