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
  "service": "ai-call-engine",
  "version": "1.0.0"
}
```

---

## 会话管理

### `POST /api/session/create`

创建新会话。

**请求体**:
```json
{
  "script": {
    "greeting": "您好，请问有什么可以帮您？",
    "system_prompt": "你是银行客服代表。"
  }
}
```

**响应示例**:
```json
{
  "session_id": "abc123",
  "status": "created"
}
```

### `POST /api/session/{session_id}/start`

启动会话，引擎开始监听音频输入。

**响应示例**:
```json
{
  "session_id": "abc123",
  "status": "listening"
}
```

### `POST /api/session/{session_id}/audio`

推送音频数据到会话。

**请求头**:
- `Content-Type: application/octet-stream`

**请求体**: PCM 音频数据 (16kHz, 16bit, mono)

**响应示例**:
```json
{
  "session_id": "abc123",
  "status": "processing",
  "queued": true
}
```

### `GET /api/session/{session_id}/info`

获取会话详细信息。

**响应示例**:
```json
{
  "session_id": "abc123",
  "state": "listening",
  "created_at": "2026-04-05T10:00:00Z",
  "events": [...],
  "transcript": "用户说的话...",
  "response": "AI 回复的内容..."
}
```

### `POST /api/session/{session_id}/end`

结束会话。

**响应示例**:
```json
{
  "session_id": "abc123",
  "status": "ended",
  "duration": 60.5
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

**响应**: PCM 音频数据

---

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 会话不存在 |
| 500 | 服务器内部错误 |
