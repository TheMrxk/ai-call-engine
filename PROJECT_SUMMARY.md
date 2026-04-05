# AI Call Engine - 项目创建总结

**创建日期**: 2026-04-05  
**版本**: 1.0.0

---

## 项目结构

```
ai-call-engine/
├── ai_call_engine_service.py    # 主服务程序
├── asr_websocket_client.py      # ASR WebSocket 客户端
├── config.py                    # 配置管理工具 ⭐
├── test_ai_call_engine.py       # 测试脚本
├── requirements.txt             # Python 依赖
├── Dockerfile.ai-engine         # Docker 镜像配置
├── docker-compose.ai-engine.yml # Docker Compose 配置
├── .env.example                 # 环境变量模板
├── deploy.sh                    # 一键部署脚本
├── nginx.conf.example           # Nginx 反向代理配置
├── .gitignore                   # Git 忽略文件
├── LICENSE                      # MIT 许可证
├── README.md                    # 项目说明
├── docs/                        # 文档目录
│   ├── API.md                   # API 文档
│   ├── CONFIGURATION.md         # 配置说明
│   ├── DEPLOYMENT.md            # 部署指南
│   └── DEVELOPMENT.md           # 开发指南
└── services/                    # 服务模块
    ├── llm_client.py            # LLM 客户端
    ├── tts_client.py            # TTS 客户端
    ├── asr_client.py            # ASR 客户端
    └── ...
```

---

## 核心功能

### 1. 独立部署
- 不依赖 FreeSWITCH
- Docker 一键启动
- HTTP API 接收音频流

### 2. ASR 语音识别
- 火山引擎豆包流式识别
- FunASR 支持
- WebRTC VAD 语音检测

### 3. LLM 大模型
- 阿里云百炼 qwen3-coder-next
- 响应时间 ~2-3 秒
- 支持 system prompt 定制

### 4. TTS 语音合成
- 火山引擎豆包 vivi 2.0
- 阿里云 NLS
- 本地缓存优化

---

## 配置工具 (config.py) ⭐

### 使用方法

```bash
# 交互式配置向导
python config.py

# 查看当前配置
python config.py show

# 设置配置项
python config.py set KEY VALUE

# 测试连接
python config.py test

# 豆包配置指南
python config.py doubao
```

### 豆包配置流程

1. 访问火山引擎控制台
2. 创建语音合成/识别应用
3. 获取 Access Token
4. 运行命令配置：
   ```bash
   python config.py set DOUBAO_ACCESS_TOKEN "你的 Token"
   ```

---

## 快速部署

### Docker Compose（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/your-org/ai-call-engine.git
cd ai-call-engine

# 2. 配置 API Key
cp .env.example .env
vi .env

# 3. 启动服务
docker-compose up -d

# 4. 验证服务
curl http://localhost:5001/api/health
```

### 一键部署脚本

```bash
# 上传部署包后
tar -xzf bank-ai-call-engine-v1.0.0.tar.gz
cd bank-ai-call-engine-v1.0.0
sudo ./deploy.sh
```

---

## 成本估算

### 单次通话（60 秒，5 轮对话）

| 项目 | 单价 | 用量 | 小计 |
|------|------|------|------|
| ASR | ¥0.002/次 | 5 次 | ¥0.01 |
| TTS | ¥0.001/次 | 5 次 | ¥0.005 |
| LLM | ¥0.008/千 tokens | 500 tokens | ¥0.004 |
| **总计** | | | **¥0.02/分钟** |

---

## API 接口

### 核心接口

```bash
# 创建会话
POST /api/session/create

# 启动会话
POST /api/session/{id}/start

# 推送音频
POST /api/session/{id}/audio

# 获取会话信息
GET /api/session/{id}/info

# 结束会话
POST /api/session/{id}/end

# TTS 合成
POST /api/tts/synthesize
```

---

## 测试验证

```bash
# 健康检查
curl http://localhost:5001/api/health

# TTS 测试
curl -X POST "http://localhost:5001/api/tts/synthesize" \
  -H "Content-Type: application/json" \
  -d '{"text": "你好，欢迎使用 AI 通话引擎"}' \
  --output test.wav

# 完整测试
python test_ai_call_engine.py
```

---

## 商业交付

### 交付内容

1. **核心文件** - Docker 镜像、服务程序
2. **配置模板** - .env.example、nginx.conf
3. **文档** - README、API 文档、部署指南
4. **脚本** - deploy.sh、package.sh

### 授权类型

| 类型 | 价格 | 权益 |
|------|------|------|
| 基础版 | ¥XX,XXX | Docker 镜像 + 部署文档 |
| 专业版 | ¥XX,XXX | 完整源码 + 1 年支持 |
| 企业版 | ¥XX,XXX | 源码 + 定制 + 永久支持 |

---

## 下一步

1. **GitHub 发布** - 创建仓库并推送代码
2. **Docker Hub** - 构建并推送镜像
3. **在线演示** - 部署测试环境
4. **营销内容** - 完善产品页面

---

## 技术栈

- **语言**: Python 3.12
- **框架**: Flask
- **容器**: Docker + Docker Compose
- **APIs**: 
  - 阿里云百炼 (LLM)
  - 火山引擎豆包 (TTS/ASR)
- **协议**: HTTP/REST, WebSocket

---

**最后更新**: 2026-04-05
