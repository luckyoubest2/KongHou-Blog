---
title: "「AI生成」Hermes Agent 远程访问完整攻略"
subtitle: "让 Desktop 客户端从公网安全连回本机后端"
date: 2026-09-11T09:30:00+08:00
draft: false
tags:
  - Hermes
  - 远程访问
  - HomeLab
  - 网络安全
categories:
  - 解决方案
collections:
  - AI生成
keywords:
  - Hermes Agent
  - Basic Auth
  - 端口转发
  - DDNS
description: "Hermes Desktop 从公网/异地访问本机后端的完整配置：Basic Auth 鉴权、路由器端口转发、DDNS、LaunchAgent 自启与故障排查。"
---

> 本文由 AI 辅助排查并整理。适用 Hermes Agent v0.21.1 及以上（2026.6 之后的版本），验证通过日期 2026-09-11，验证环境 macOS + 公网 IPv4。目标：让 Hermes Desktop 客户端从公网/异地区访问本机的 Hermes 后端。

## 0. 架构概览

```
┌──────────────────┐                          ┌─────────────────────────┐
│ 远端机器          │                          │ 本机（家庭/办公网络）    │
│                  │ ───── HTTPS/WSS ────────>│                         │
│ Hermes Desktop   │   http://公网IP:9119     │ Hermes Backend (serve)  │
│ App (Electron)   │                          │ --host 0.0.0.0:9119     │
│                  │ <─── JSON-RPC + WS ───── │                         │
└──────────────────┘                          └─────────────────────────┘
```

需要打通 3 件事：

1. **本机**：启动对外可达的 Hermes 后端服务（默认端口 9119）
2. **网络**：路由器做端口转发，把公网 IP:9119 映射到本机 IP:9119
3. **远端**：在 Hermes Desktop App 里添加远程访问入口，登录认证

## 1. 前置条件

| 项 | 说明 |
|---|---|
| Hermes Agent | ≥ v0.21.1（2026.6 之前的版本鉴权机制不同，不适用本文） |
| 公网 IP | 本机有可用的 IPv4 或 IPv6 公网地址 |
| 路由器管理权限 | 用于配置端口转发 |
| macOS 防火墙 | 允许 Python 入站连接（见 §3.3） |

## 2. 本机配置

### 2.1 启用 Basic Auth 鉴权

**关键背景**：2026 年 6 月 hermes-0day 安全事件后，Hermes 对**任何非 loopback 绑定**（包括 `0.0.0.0`）强制启用鉴权门。`--insecure` 已废弃，**必须**配置用户名/密码。

在 `~/.hermes/.env` 中追加以下三行：

```bash
# 远程访问用的 Basic Auth（公网 0.0.0.0 绑定强制要求）
HERMES_DASHBOARD_BASIC_AUTH_USERNAME=<你的用户名>
HERMES_DASHBOARD_BASIC_AUTH_PASSWORD=<强密码，建议 20+ 字符>
HERMES_DASHBOARD_BASIC_AUTH_SECRET=<随机 32+ 字节，base64 编码>
```

**生成强凭据示例**：

```bash
# 生成 20 位强密码
openssl rand -base64 18 | tr -d '/+=' | head -c 20

# 生成 32 字节 base64 secret
openssl rand -base64 32
```

### 2.2 停掉 Desktop 自带的 loopback serve

Hermes Desktop App 默认自带一个绑定 `127.0.0.1` 的 serve 进程（端口为 0，即 OS 随机分配），它**只对桌面 App 自己可见**，远程客户端连不到。先停掉它，避免端口冲突：

```bash
pkill -f 'hermes_cli.main serve'
sleep 2

# 验证：应该看不到任何 hermes_cli.main serve 进程
ps -eo pid,command | grep 'hermes_cli.main serve' | grep -v grep
```

### 2.3 启动对外可达的 serve

```bash
nohup ~/.hermes/hermes-agent/venv/bin/hermes \
  serve --host 0.0.0.0 --port 9119 \
  > ~/.hermes/logs/serve-remote.log 2>&1 &

sleep 3

# 验证：端口监听 + auth provider 已注册
lsof -nP -iTCP:9119 -sTCP:LISTEN
curl -s http://127.0.0.1:9119/api/auth/providers | python3 -m json.tool
```

**期望输出**：

```json
{
    "providers": [
        {
            "name": "basic",
            "display_name": "Username & Password",
            "supports_password": true
        }
    ]
}
```

看到 `"basic"` provider 即表示鉴权门已正确启用。

### 2.4 本机自测

```bash
# 不带凭证：可能 200（status 公开）或 401（取决于版本）
curl -i http://127.0.0.1:9119/api/status

# 带凭证：必须 200
curl -u '<用户名>:<密码>' http://127.0.0.1:9119/api/status
```

## 3. 网络配置

### 3.1 路由器端口转发

登录路由器后台（通常是 `192.168.1.1` 或 `192.168.3.1`），添加一条端口转发规则：

| 字段 | 值 |
|---|---|
| 服务名称 | hermes-remote |
| 外部端口 | `9119` |
| 内部 IP | 本机内网 IP（如 `192.168.1.100`） |
| 内部端口 | `9119` |
| 协议 | TCP |

### 3.2 DDNS（可选但推荐）

如果你的公网 IP 是动态的（运营商 DHCP），需要 DDNS 自动同步：

- **群晖 NAS 用户**：Synology DDNS 已经支持自定义子域名，把分配给你的子域名指向路由器 WAN IP 即可
- **通用方案**：在路由器或 NAS 上跑 DDNS 客户端（dnspod / cloudflare / no-ip 等）

### 3.3 macOS 防火墙放行

```bash
# 临时方案：完全关闭入站阻止（不推荐）
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off

# 推荐方案：放行 Hermes 的 Python 二进制
sudo /usr/libexec/ApplicationFirewall/socketfilterfw \
  --add ~/.hermes/hermes-agent/venv/bin/python3
sudo /usr/libexec/ApplicationFirewall/socketfilterfw \
  --unblock ~/.hermes/hermes-agent/venv/bin/python3
```

### 3.4 公网连通性验证

从**公网设备**（如手机开 4G、异地的电脑）测试：

```bash
curl -u '<用户名>:<密码>' http://<公网IP或域名>:9119/api/status
```

期望返回 200 和 JSON 状态信息。如果超时或连接被拒：

- 检查路由器端口转发规则是否生效
- 检查 ISP 是否做了 CGNAT（运营商级 NAT）→ 这种情况下即使路由器配了端口转发也没用
- 用 `traceroute -n -m 5 -w 2 <公网IP>` 看第一跳是不是 `100.64.x.x` 或 `10.x.x.x`，是的话就是 CGNAT

## 4. 远端 Hermes Desktop 配置

### 4.1 在 Desktop App 中添加远程入口

> ⚠️ **关键细节**：在 Desktop App 中配置远程访问时，必须**先添加远程入口**，然后**点击"登录认证"按钮完成认证**（而非直接保存 URL 和 token）。
> Profile 内的 token 是给本地 loopback 后端用的，不能直接用于远程连接。

操作步骤：

1. 打开 Hermes Desktop App
2. 进入 **Settings → Gateways**（或 **Remote Gateway**，具体菜单项因版本而异）
3. 点击 **Add Remote Connection** / **添加远程访问**
4. 填写：
   - **Remote URL**：`http://<公网IP或域名>:9119`
   - **Username**：§2.1 设置的用户名
   - **Password**：§2.1 设置的密码
5. **点击"登录认证"按钮**（不是直接保存）—— 这一步会触发 OAuth/Sign-in 流程，完成远程后端的握手认证
6. 看到"Connected / 已连接"状态后即可使用

### 4.2 环境变量方式（可选）

如果 Desktop App 是用脚本或 CLI 启动的，可以在启动前设置环境变量：

```bash
export HERMES_DESKTOP_REMOTE_URL="http://<公网IP>:9119"
export HERMES_DESKTOP_REMOTE_USERNAME="<用户名>"
export HERMES_DESKTOP_REMOTE_PASSWORD="<密码>"

# 然后启动 Desktop App
open -a Hermes
```

## 5. 开机自启（可选）

为了让 serve 在系统重启后自动起来，写一个 LaunchAgent：

```bash
mkdir -p ~/.hermes/logs

cat > ~/Library/LaunchAgents/ai.hermes.serve.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>ai.hermes.serve</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Users/<你的用户名>/.hermes/hermes-agent/venv/bin/hermes</string>
    <string>serve</string>
    <string>--host</string><string>0.0.0.0</string>
    <string>--port</string><string>9119</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>/Users/<你的用户名>/.hermes/logs/serve-remote.log</string>
  <key>StandardErrorPath</key><string>/Users/<你的用户名>/.hermes/logs/serve-remote.error.log</string>
</dict>
</plist>
EOF

launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.hermes.serve.plist
```

> 注意：把 `<你的用户名>` 替换为实际的 macOS 用户名。

## 6. 故障排查

| 症状 | 原因 | 修复 |
|---|---|---|
| 远端 Desktop 连不上，公网 IP 探测超时 | 路由器端口转发未生效 / ISP CGNAT | 验证路由器规则；用 `traceroute` 排查 CGNAT |
| `/api/auth/providers` 没有 `basic` provider | `.env` 里 Basic Auth 配置没生效 | 检查拼写、确认 `.env` 没被 `#` 注释、重启 serve |
| 远端 Desktop 报"401 Unauthorized" | 用户名/密码错了，或公网绑定没启鉴权门 | 用 §2.4 的 `curl -u` 自测；确认 `--host 0.0.0.0` |
| Desktop 自带 serve 占了 9119 端口 | pkill 没杀掉，Desktop App 自动重启了它 | 先关掉 Desktop App，再启 serve；或换端口 |
| WebSocket 连上后立刻断开 | 鉴权通过但 token 失效 / Origin 检查失败 | 确认 `.env` 中 token 与 Desktop 中保存的一致 |
| Desktop 报"loopback-only"错误 | URL 写成了 `127.0.0.1` 而非公网 IP | 改用真实公网 IP 或 DDNS 域名 |

## 7. 安全建议

1. **强密码**：Basic Auth 密码至少 20 字符，包含大小写字母 + 数字 + 符号
2. **限制来源 IP**：路由器层面限制 9119 端口只接受常用 IP 段
3. **使用 Tailscale**：相比公网开放端口，Tailscale 虚拟组网更安全（不需要路由器端口转发）
4. **定期轮换 secret**：每隔几个月更新 `HERMES_DASHBOARD_BASIC_AUTH_SECRET`
5. **启用 HTTPS**：生产环境建议套 Cloudflare Tunnel 或自建反向代理（caddy / nginx）提供 TLS

## 8. 备选方案对比

| 方案 | 优点 | 缺点 | 适用 |
|---|---|---|---|
| **公网 + Basic Auth**（本文） | 配置简单，跨网络可用 | 需路由器配置 / 暴露端口 | 有公网 IP 的家庭/办公环境 |
| **Tailscale 虚拟组网** | 不开公网端口，安全 | 需两端装客户端 | 安全性优先的场景 |
| **Cloudflare Tunnel** | 隐藏真实 IP，自带 HTTPS | 配置稍复杂 | 公网 IP 动态 / 想用域名 |
| **SSH 反向隧道** | 纯命令行，无需额外服务 | 远端每次需 SSH | 临时调试 |

## 9. 参考链接

- [Hermes Web Dashboard 文档](https://hermes-agent.nousresearch.com/docs/user-guide/features/web-dashboard)
- [Hermes Desktop 文档](https://hermes-agent.nousresearch.com/docs/user-guide/desktop)
- [Hermes Agent 安装](https://hermes-agent.nousresearch.com/docs/getting-started/installation)
