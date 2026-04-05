# 聊天记录导出 API 使用指南

## 概述

AI Call Engine 支持将以 Markdown 格式导出用户与 AI 的完整聊天记录，并提供结构化数据接口，方便后期使用大模型整理用户信息。

---

## API 接口

### 1. 导出 Markdown 聊天记录

**接口**: `GET /api/session/{session_id}/export`

**描述**: 导出 Markdown 格式的聊天记录文件

**参数**:
- `session_id` (路径参数): 会话 ID

**响应**:
- Content-Type: `text/markdown`
- Content-Disposition: `attachment; filename="conversation_{session_id}.md"`

**示例**:
```bash
curl -X GET "http://localhost:5001/api/session/abc123/export" \
  -o conversation.md
```

**Markdown 内容示例**:
```markdown
# AI 通话记录

## 基本信息

- **会话 ID**: `abc123`
- **开始时间**: 2026-04-05 14:30:00
- **结束时间**: 2026-04-05 14:35:30
- **通话时长**: 330.0 秒
- **对话轮数**: 5
- **最终状态**: ended

## 对话内容

### 14:30:05 - 👤 客户

我想咨询一下你们的贷款利率

### 14:30:08 - 🤖 AI 客服

您好，我行目前提供多种贷款产品，包括个人消费贷款、住房贷款、经营贷款等。请问您具体想了解哪种贷款呢？

### 14:30:15 - 👤 客户

个人消费贷款，大概 10 万左右

### 14:30:18 - 🤖 AI 客服

好的，我行个人消费贷款额度 10 万元的年利率约为 4.35%，贷款期限最长可达 5 年...

## 系统配置

**系统提示词**: 你是一个专业的银行客服代表...

## 原始数据 (JSON)

```json
{
  "session_id": "abc123",
  "started_at": "2026-04-05T14:30:00",
  "turns": [...]
}
```
```

---

### 2. 获取会话摘要数据

**接口**: `GET /api/session/{session_id}/summary`

**描述**: 获取结构化的会话数据，用于大模型整理用户信息

**参数**:
- `session_id` (路径参数): 会话 ID

**响应示例**:
```json
{
  "success": true,
  "data": {
    "session_id": "abc123",
    "basic_info": {
      "started_at": "2026-04-05T14:30:00",
      "ended_at": "2026-04-05T14:35:30",
      "duration": 330.0,
      "turn_count": 5
    },
    "conversation": [
      {
        "role": "user",
        "text": "我想咨询一下你们的贷款利率",
        "timestamp": 1712326205.123
      },
      {
        "role": "assistant",
        "text": "您好，我行目前提供多种贷款产品...",
        "timestamp": 1712326208.456
      }
    ],
    "customer_info": {},
    "full_transcript": "user: 我想咨询一下你们的贷款利率\nassistant: 您好，我行目前提供多种贷款产品..."
  }
}
```

---

### 3. 更新客户信息

**接口**: `POST /api/session/{session_id}/customer-info`

**描述**: 大模型分析对话后，调用此接口存储提取的客户信息

**参数**:
- `session_id` (路径参数): 会话 ID
- `info` (JSON 体): 客户信息键值对

**请求示例**:
```bash
curl -X POST "http://localhost:5001/api/session/abc123/customer-info" \
  -H "Content-Type: application/json" \
  -d '{
    "interest": "个人消费贷款",
    "target_amount": "100000",
    "sentiment": "positive"
  }'
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

## 完整工作流程

### 场景：使用大模型整理用户信息

```
1. 创建会话并通话
   POST /api/session/create
   POST /api/session/{id}/start
   (推送音频...)

2. 通话结束后导出记录
   GET /api/session/{id}/export
   → 获得 conversation_{id}.md

3. 获取结构化数据
   GET /api/session/{id}/summary
   → 获得 JSON 格式的完整对话数据

4. 发送给大模型分析
   (调用 LLM API，分析对话内容)
   
   Prompt 示例:
   "请分析以下对话，提取客户的关键信息:
   - 感兴趣的產品
   - 预算/金额
   - 意向程度
   - 联系方式（如果有）
   
   对话内容：{full_transcript}"

5. 存储大模型返回的客户信息
   POST /api/session/{id}/customer-info
   {
     "info": {
       "interest": "个人消费贷款",
       "target_amount": "100000",
       "sentiment": "positive"
     }
   }

6. （可选）再次导出 Markdown
   GET /api/session/{id}/export
   → Markdown 中会包含客户信息摘要
```

---

## Python 示例代码

```python
import requests
import json

BASE_URL = "http://localhost:5001"

# 1. 创建会话
resp = requests.post(f"{BASE_URL}/api/session/create", json={
    "script": {
        "greeting": "您好，请问有什么可以帮您？",
        "system_prompt": "你是银行客服代表。"
    }
})
session_id = resp.json()['session_id']

# 2. 启动会话
requests.post(f"{BASE_URL}/api/session/{session_id}/start")

# ... 推送音频 ...

# 3. 等待通话结束
time.sleep(60)

# 4. 导出 Markdown 聊天记录
resp = requests.get(f"{BASE_URL}/api/session/{session_id}/export")
with open(f"conversation_{session_id}.md", "w", encoding="utf-8") as f:
    f.write(resp.text)
print(f"已导出聊天记录：conversation_{session_id}.md")

# 5. 获取结构化数据
resp = requests.get(f"{BASE_URL}/api/session/{session_id}/summary")
data = resp.json()['data']

# 6. 使用大模型分析（示例）
from llm_client import LLMClient  # 假设你有 LLM 客户端

llm = LLMClient(api_key="xxx", provider="dashscope_coding")

prompt = f"""请分析以下客服对话，提取客户的关键信息：

对话内容:
{data['full_transcript']}

请返回 JSON 格式:
{{
  "interest": "客户感兴趣的产品",
  "budget": "客户提到的金额或预算",
  "sentiment": "客户意向程度 (positive/neutral/negative)",
  "contact": "客户留下的联系方式（如果有）",
  "notes": "其他重要信息"
}}
"""

result = llm.chat([{"role": "user", "content": prompt}])
customer_info = json.loads(result)

# 7. 存储客户信息
requests.post(
    f"{BASE_URL}/api/session/{session_id}/customer-info",
    json={"info": customer_info}
)

print(f"已存储客户信息：{customer_info}")
```

---

## Markdown 文件结构

导出的 Markdown 文件包含以下部分：

| 章节 | 说明 |
|------|------|
| 基本信息 | 会话 ID、时间戳、时长、轮数、状态 |
| 客户信息摘要 | 大模型提取的客户信息（如果有） |
| 对话内容 | 按时间顺序排列的对话，带角色标识 |
| 系统配置 | 系统提示词、问候语、结束语 |
| 原始数据 (JSON) | 完整的 JSON 格式数据，便于程序处理 |

---

## 最佳实践

### 1. 定时导出
```bash
# 每天导出前一天的聊天记录
0 2 * * * python export_daily_conversations.py
```

### 2. 批量分析
```python
# 批量获取所有会话并分析
for session_id in session_ids:
    summary = get_summary(session_id)
    info = analyze_with_llm(summary['full_transcript'])
    save_customer_info(session_id, info)
```

### 3. CRM 集成
```python
# 将客户信息同步到 CRM 系统
def sync_to_crm(session_id, customer_info):
    if 'contact' in customer_info:
        crm.create_lead(
            phone=customer_info['contact'],
            interest=customer_info['interest'],
            source='ai_call'
        )
```

---

## 注意事项

1. **隐私保护**: 导出的聊天记录可能包含客户敏感信息，请妥善保管
2. **存储策略**: 建议设置自动归档和清理策略
3. **合规性**: 确保符合当地数据保护法规（如 GDPR、个人信息保护法等）

---

**最后更新**: 2026-04-05
