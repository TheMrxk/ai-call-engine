# 配置说明

详细配置参数说明。

---

## LLM 配置

### LLM_API_KEY

**必填**: 是  
**说明**: 阿里云百炼 API Key  
**示例**: `sk-sp-xxxxxxxxxxxxxxxx`  
**申请地址**: https://dashscope.console.aliyun.com/apiKey

### LLM_PROVIDER

**必填**: 否  
**默认**: `dashscope_coding`  
**可选**: `dashscope_coding`, `dashscope`, `deepseek`, `openai`

### LLM_MODEL

**必填**: 否  
**默认**: `qwen3-coder-next`  
**可选**: `qwen3-coder-next`, `qwen-plus`, `qwen-turbo`, `deepseek-chat`

---

## TTS 配置

### TTS_PROVIDER

**必填**: 否  
**默认**: `doubao`  
**可选**: `doubao`, `aliyun`

### DOUBAO_APPID

**必填**: 否  
**默认**: `2058216235`  
**说明**: 火山引擎豆包 APPID

### DOUBAO_ACCESS_TOKEN

**必填**: 是  
**说明**: 火山引擎豆包 Access Token  
**申请地址**: https://console.volcengine.com/speech/service

### DOUBAO_SPEAKER

**必填**: 否  
**默认**: `zh_female_vv_uranus_bigtts`  
**说明**: 豆包 TTS 音色 (vivi 2.0)

---

## ASR 配置

### ASR_PROVIDER

**必填**: 否  
**默认**: `volcengine_doubao`  
**可选**: `volcengine_doubao`, `funasr`

### DOUBAO_ASR_RESOURCE_ID

**必填**: 否  
**默认**: `volc.seedasr.sauc.duration`  
**说明**: 豆包 ASR 资源 ID (小时版计费)

### DOUBAO_ASR_WS_URL

**必填**: 否  
**默认**: `wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_async`  
**说明**: 豆包 ASR WebSocket 地址

---

## 服务配置

### PORT

**必填**: 否  
**默认**: `5001`  
**说明**: 服务端口

### HOST

**必填**: 否  
**默认**: `0.0.0.0`  
**说明**: 服务地址

---

## 配置工具使用

### 交互式向导

```bash
python config.py
```

### 命令行配置

```bash
# 设置配置项
python config.py set KEY VALUE

# 示例
python config.py set LLM_API_KEY "sk-sp-xxx"
python config.py set DOUBAO_ACCESS_TOKEN "xxx"
```

### 查看配置

```bash
python config.py show
```

### 测试连接

```bash
python config.py test
```

### 豆包配置指南

```bash
python config.py doubao
```
