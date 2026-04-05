# 开发指南

本地开发环境配置。

---

## 开发环境要求

- Python 3.12+
- Docker 20.10+
- Git

---

## 本地运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
vi .env
```

### 3. 启动服务

```bash
python ai_call_engine_service.py --port 5001
```

### 4. 测试

```bash
python test_ai_call_engine.py
```

---

## 代码结构

```
ai-call-engine/
├── ai_call_engine_service.py  # 主服务
├── asr_websocket_client.py    # ASR 客户端
├── config.py                   # 配置工具
├── test_ai_call_engine.py      # 测试脚本
├── services/
│   ├── llm_client.py          # LLM 客户端
│   ├── tts_client.py          # TTS 客户端
│   └── asr_client.py          # ASR 客户端
├── docs/                       # 文档
└── .env.example                # 配置模板
```

---

## 构建 Docker 镜像

```bash
# 构建镜像
docker build -f Dockerfile.ai-engine -t ai-call-engine:latest .

# 运行容器
docker run -p 5001:5001 --env-file .env ai-call-engine:latest
```

---

## 测试

### 单元测试

```bash
pytest tests/
```

### 集成测试

```bash
python test_ai_call_engine.py
```

### API 测试

```bash
# 健康检查
curl http://localhost:5001/api/health

# TTS 测试
curl -X POST "http://localhost:5001/api/tts/synthesize" \
  -H "Content-Type: application/json" \
  -d '{"text": "测试"}' \
  --output test.wav
```

---

## 代码规范

- 遵循 PEP 8
- 使用 4 空格缩进
- 函数添加文档字符串
- 关键逻辑添加注释

---

## 提交规范

```
feat: 添加新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试
chore: 构建/工具
```

示例：
```bash
git commit -m "feat: 添加 ASR 断线重连机制"
```
