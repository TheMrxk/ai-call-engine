# AI Call Engine - API 文档

完整 API 参考文档。

---

## 概述

AI Call Engine 提供 RESTful HTTP API 用于管理会话和处理音频流。

**基础 URL**: `http://localhost:5001`

---

## 健康检查

### `GET /api/health`

检查服务健康状态。

**响应示例**:
```json
{
  "status": "ok",
  "timestamp": 1712326200
}
```

---

## 会话管理

### `POST /api/session/create`

创建新会话。

**请求体**:
```json
{
  "session_id": "custom-id-123",  // 可选，不填则自动生成
  "config": {
    "max_duration": 300,
    "max_turns": 10,
    "silence_timeout": 10.0
  },
  "script": {
    "greeting": "您好，请问有什么可以帮您？",
    "system_prompt": "你是银行客服代表。",
    "mock_llm": false
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "session_id": "abc123"
}
```

### `POST /api/session/{session_id}/start`

启动会话，引擎开始监听音频输入。

**响应示例**:
```json
{
  "success": true
}
```

### `POST /api/session/{session_id}/audio`

推送音频数据到会话。

**请求头**:
- `Content-Type: application/octet-stream` 或 `application/json`

**请求体**: 
- PCM 音频数据 (16kHz, 16bit, mono)
- 或 JSON: `{"audio": "base64_encoded_audio"}`

**响应示例**:
```json
{
  "success": true
}
```

### `GET /api/session/{session_id}/info`

获取会话详细信息。

**响应示例**:
```json
{
  "success": true,
  "data": {
    "session_id": "abc123",
    "state": "listening",
    "turn_count": 3,
    "created_at": 1712326200,
    "started_at": 1712326205,
    "duration": 120.5,
    "turns": [
      {
        "turn_id": 1,
        "role": "user",
        "text": "我想咨询贷款",
        "timestamp": 1712326210
      },
      {
        "turn_id": 1,
        "role": "assistant",
        "text": "好的，请问您想了解哪种贷款？",
        "timestamp": 1712326215
      }
    ]
  }
}
```

### `POST /api/session/{session_id}/end`

结束会话。

**响应示例**:
```json
{
  "success": true
}
```

---

## 聊天记录导出

### `GET /api/session/{session_id}/export`

导出 Markdown 格式的聊天记录。

**响应**:
- Content-Type: `text/markdown`
- Content-Disposition: `attachment; filename="conversation_{session_id}.md"`

**示例**:
```bash
curl -X GET "http://localhost:5001/api/session/abc123/export" -o conversation.md
```

**Markdown 内容包含**:
- 基本信息（会话 ID、时间、时长、轮数）
- 客户信息摘要（如果有）
- 完整对话内容（带时间戳和角色标识）
- 系统配置
- 原始 JSON 数据

---

### `GET /api/session/{session_id}/summary`

获取会话摘要数据，用于大模型整理用户信息。

**响应示例**:
```json
{
  "success": true,
  "data": {
    "session_id": "abc123",
    "basic_info": {
      "started_at": "2026-04-05T14:30:00",
      "duration": 330.0,
      "turn_count": 5
    },
    "conversation": [
      {"role": "user", "text": "...", "timestamp": 1712326200},
      {"role": "assistant", "text": "...", "timestamp": 1712326205}
    ],
    "customer_info": {},
    "full_transcript": "user: ...\nassistant: ..."
  }
}
```

---

### `POST /api/session/{session_id}/customer-info`

更新客户信息（大模型分析后调用）。

**请求体**:
```json
{
  "info": {
    "interest": "个人消费贷款",
    "target_amount": "100000",
    "sentiment": "positive"
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "customer_info": {
    "interest": "个人消费贷款",
    "target_amount": "100000",
    "sentiment": "positive"
  }
}
```

---

## TTS 接口

### `POST /api/tts/synthesize`

合成语音。

**请求体**:
```json
{
  "text": "您好，欢迎使用银行 AI 客服服务。"
}
```

**响应**: PCM 音频数据 (audio/wav)

**示例**:
```bash
curl -X POST "http://localhost:5001/api/tts/synthesize" \
  -H "Content-Type: application/json" \
  -d '{"text": "测试"}' \
  --output test.wav
```

---

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 会话不存在 |
| 500 | 服务器内部错误 |

---

## 使用示例

### 完整对话流程

```bash
# 1. 创建会话
SESSION_ID=$(curl -X POST "http://localhost:5001/api/session/create" \
  -H "Content-Type: application/json" \
  -d '{"script": {"greeting": "您好"}}' | jq -r '.session_id')

# 2. 启动会话
curl -X POST "http://localhost:5001/api/session/$SESSION_ID/start"

# 3. 推送音频
curl -X POST "http://localhost:5001/api/session/$SESSION_ID/audio" \
  --data-binary @audio.pcm

# 4. 查看状态
curl "http://localhost:5001/api/session/$SESSION_ID/info"

# 5. 导出聊天记录
curl "http://localhost:5001/api/session/$SESSION_ID/export" -o conversation.md

# 6. 结束会话
curl -X POST "http://localhost:5001/api/session/$SESSION_ID/end"
```

---

详见 [EXPORT_API.md](EXPORT_API.md) 了解聊天记录导出和客户信息整理的完整流程。
