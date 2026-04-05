# 部署指南

生产环境部署详细说明。

---

## 系统要求

### 最低配置
- CPU: 2 核
- 内存：4GB
- 存储：10GB
- 网络：100Mbps

### 推荐配置
- CPU: 4 核
- 内存：8GB
- 存储：20GB SSD
- 网络：1Gbps

---

## Docker 部署（推荐）

### 1. 安装 Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh

# CentOS
yum install -y yum-utils
yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
yum install docker-ce docker-ce-cli containerd.io
```

### 2. 配置环境变量

```bash
cp .env.example .env
vi .env
```

必要配置：
- `LLM_API_KEY` - 阿里云百炼 API Key
- `DOUBAO_ACCESS_TOKEN` - 火山引擎豆包 Access Token

### 3. 启动服务

```bash
docker-compose up -d
```

### 4. 验证服务

```bash
curl http://localhost:5001/api/health
```

---

## 生产环境配置

### Nginx 反向代理

```bash
# 安装 Nginx
apt install nginx

# 配置
cp nginx.conf.example /etc/nginx/nginx.conf

# 启动
systemctl start nginx
```

### HTTPS 证书

```bash
# 安装 Certbot
apt install certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d your-domain.com
```

### 防火墙配置

```bash
# 开放端口
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

---

## 监控与日志

### 查看日志

```bash
# 容器日志
docker-compose logs -f ai-call-engine

# Nginx 日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### 健康检查

```bash
# 定时检查
watch -n 5 'curl -s http://localhost:5001/api/health'
```

---

## 故障排查

### 服务无法启动

```bash
# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs ai-call-engine
```

### API 调用失败

```bash
# 检查配置
python config.py show

# 测试连接
python config.py test
```

### 内存不足

```bash
# 查看资源使用
docker stats

# 重启容器
docker-compose restart
```
