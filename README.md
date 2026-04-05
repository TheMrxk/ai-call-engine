# AI Call Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Python 3.12](https://img.shields.io/badge/python-3.12-green.svg)](https://www.python.org/)

**AI 通话引擎** - 独立的 AI 语音对话引擎服务，支持 ASR（语音识别）→ LLM（大模型）→ TTS（语音合成）完整链路。

无需 FreeSWITCH，通过 HTTP API 即可集成到现有电话系统中。

---

## ✨ 特性

- 🔌 **独立部署** - 不依赖 FreeSWITCH，Docker 一键启动
- 🎤 **ASR 语音识别** - 支持火山引擎豆包、FunASR 等
- 🧠 **LLM 大模型** - 支持阿里云百炼、DeepSeek、OpenAI 等
- 🔊 **TTS 语音合成** - 支持火山引擎豆包、阿里云等
- 📡 **HTTP API** - 简单易用的 RESTful API
- 🔄 **实时对话** - 支持双向流式音频传输
- 💰 **低成本** - 按量付费，单次通话成本约 ¥0.02/分钟

---

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/your-org/ai-call-engine.git
cd ai-call-engine

# 2. 配置 API Key
cp .env.example .env
vi .env  # 填写必要的 API Key

# 3. 启动服务
docker-compose up -d

# 4. 验证服务
curl http://localhost:5001/api/health
```

### 方式二：直接运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
export LLM_API_KEY="sk-sp-xxxxxxxx"
export DOUBAO_ACCESS_TOKEN="xxxxxxxx"

# 3. 启动服务
python ai_call_engine_service.py --port 5001

# 4. 测试
python test_ai_call_engine.py
```

---

## 📦 配置指南

### 配置命令（推荐）

使用配置向导快速配置 ASR/TTS：

```bash
# 运行配置向导
python config.py

# 或命令行配置
python config.py set llm_api_key "sk-sp-xxxxxxxx"
python config.py set doubao_access_token "xxxxxxxx"
python config.py set asr_provider "volcengine_doubao"
```

### 手动配置

编辑 `.env` 文件：

```bash
# ========================================
# LLM 配置（阿里云百炼）
# ========================================
LLM_API_KEY=sk-sp-xxxxxxxxxxxxxxxx
LLM_PROVIDER=dashscope_coding
LLM_MODEL=qwen3-coder-next

# ========================================
# TTS 配置（火山引擎豆包）
# ========================================
TTS_PROVIDER=doubao
DOUBAO_APPID=2058216235
DOUBAO_ACCESS_TOKEN=xxxxxxxxxxxxxxxx
DOUBAO_SPEAKER=zh_female_vv_uranus_bigtts

# ========================================
# ASR 配置（火山引擎豆包）
# ========================================
ASR_PROVIDER=volcengine_doubao
DOUBAO_ASR_RESOURCE_ID=volc.seedasr.sauc.duration
DOUBAO_ASR_WS_URL=wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_async
```

---

## 🔧 配置火山引擎豆包

### 1. 创建豆包应用

1. 访问 [火山引擎控制台](https://console.volcengine.com/speech/service)
2. 登录/注册账号
3. 进入「语音合成」或「语音识别」服务
4. 创建新应用

### 2. 获取 Access Token

```bash
# 方式一：使用配置向导
python config.py config_doubao

# 方式二：手动获取
# 访问：https://console.volcengine.com/speech/service
# 在应用详情页找到 Access Token
```

### 3. 验证配置

```bash
# 测试 TTS
curl -X POST "http://localhost:5001/api/tts/synthesize" \
  -H "Content-Type: application/json" \
  -d '{"text": "你好，欢迎使用 AI 通话引擎"}' \
  --output test.wav

# 测试连接
python config.py test_connection
```

---

## 📖 API 文档

### 核心接口

#### 1. 创建会话

```bash
curl -X POST "http://localhost:5001/api/session/create" \
  -H "Content-Type: application/json" \
  -d '{
    "script": {
      "greeting": "您好，请问有什么可以帮您？",
      "system_prompt": "你是银行客服代表。"
    }
  }'
```

#### 2. 启动会话

```bash
curl -X POST "http://localhost:5001/api/session/{session_id}/start"
```

#### 3. 推送音频

```bash
curl -X POST "http://localhost:5001/api/session/{session_id}/audio" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @audio.pcm
```

#### 4. 获取会话信息

```bash
curl "http://localhost:5001/api/session/{session_id}/info"
```

#### 5. TTS 合成

```bash
curl -X POST "http://localhost:5001/api/tts/synthesize" \
  -H "Content-Type: application/json" \
  -d '{"text": "您好，欢迎使用银行 AI 客服服务。"}' \
  --output response.wav
```

完整 API 文档请参阅 [API.md](docs/API.md)

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    客户电话呼入                          │
│                           │                             │
│                           ▼                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │  音频输入    │───▶│    ASR      │───▶│    LLM      │ │
│  │  (PCM)      │    │  (语音识别)  │    │ (大模型)    │ │
│  └─────────────┘    └─────────────┘    └─────────────┘ │
│                                            │            │
│                                            ▼            │
│  ┌─────────────┐                         ┌─────────────┐│
│  │  音频输出    │◀────────────────────────│    TTS      ││
│  │  (PCM)      │                         │ (语音合成)  ││
│  └─────────────┘                         └─────────────┘│
└─────────────────────────────────────────────────────────┘
```

---

## 💰 成本估算

### 单次通话成本（60 秒，5 轮对话）

| 项目 | 单价 | 用量 | 小计 |
|------|------|------|------|
| ASR | ¥0.002/次 | 5 次 | ¥0.01 |
| TTS | ¥0.001/次 | 5 次 | ¥0.005 |
| LLM | ¥0.008/千 tokens | 500 tokens | ¥0.004 |
| **总计** | | | **¥0.02/分钟** |

### 月度成本示例

| 场景 | 通话量 | 月成本 |
|------|--------|--------|
| 小型客服 | 100 通/天 × 3 分钟 | ¥180 |
| 中型客服 | 500 通/天 × 3 分钟 | ¥900 |
| 大型客服 | 2000 通/天 × 3 分钟 | ¥3,600 |

---

## 🔍 故障排查

### 服务无法启动

```bash
# 查看日志
docker-compose logs ai-call-engine

# 检查配置
python config.py show

# 测试连接
python config.py test_connection
```

### API 调用失败

```bash
# 检查环境变量
python config.py show

# 健康检查
curl http://localhost:5001/api/health

# 查看服务状态
docker-compose ps
```

### TTS/ASR 失败

```bash
# 测试 TTS
curl -X POST "http://localhost:5001/api/tts/synthesize" \
  -H "Content-Type: application/json" \
  -d '{"text": "测试"}' \
  --output test.wav

# 检查豆包配置
python config.py config_doubao
```

---

## 📚 相关文档

- [部署指南](docs/DEPLOYMENT.md) - 生产环境部署
- [API 文档](docs/API.md) - 完整 API 参考
- [配置说明](docs/CONFIGURATION.md) - 详细配置参数
- [开发指南](docs/DEVELOPMENT.md) - 本地开发环境

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

```bash
# Fork 项目
git fork https://github.com/your-org/ai-call-engine

# 创建分支
git checkout -b feature/your-feature

# 提交代码
git commit -m "Add your feature"

# 推送分支
git push origin feature/your-feature

# 提交 PR
```

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 📞 支持

- 📧 Email: support@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/your-org/ai-call-engine/issues)
- 💬 讨论区：[Discussions](https://github.com/your-org/ai-call-engine/discussions)

---

**最后更新**: 2026-04-05
