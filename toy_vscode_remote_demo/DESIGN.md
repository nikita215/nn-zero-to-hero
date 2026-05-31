# Toy VS Code Remote 设计实现文档

## 1. 项目目标

本项目基于前面的 Toy SSH demo，继续实现一个“教学版 VS Code Remote”。

它不追求兼容真实 VS Code Remote 协议，而是用最小代码演示 VS Code Remote 的核心思想：

- 本地只负责交互和显示
- 远程负责访问文件、执行命令、搜索代码
- 本地和远程之间通过安全通道交换 RPC 消息

真实 VS Code Remote 的组成非常复杂，包括 VS Code Server、扩展宿主、文件系统 provider、语言服务、调试适配器、终端服务、端口转发等。本 demo 只实现最核心的远程工作区能力。

## 2. 与 Toy SSH 的关系

Toy SSH demo 已经实现了这些基础能力：

- TCP client/server
- 服务端主机密钥
- known hosts 指纹校验
- X25519 临时密钥交换
- HKDF 派生会话密钥
- AES-GCM 加密消息
- 用户名密码认证
- 远程命令执行

Toy VS Code Remote 在此基础上继续扩展：

- 不再只执行一次命令
- 连接建立后保持长连接
- 在同一条加密通道上承载多个远程开发请求
- 增加远程文件系统操作
- 增加远程文本搜索
- 增加交互式 client REPL
- 用 workspace root 限制远程文件访问范围

## 3. 总体架构

```text
Local Machine
  toyremote.client
    |
    | TCP + Toy SSH secure transport
    |
Remote Machine
  toyremote.server
    |
    | workspace operations
    |
  project files / shell commands
```

本地客户端负责：

- 建立连接
- 校验服务端主机指纹
- 输入命令
- 发送 RPC 请求
- 显示远程结果

远程服务端负责：

- 监听 TCP 端口
- 完成安全握手
- 验证用户身份
- 管理远程 workspace
- 执行文件读写、目录列表、搜索、命令执行

## 4. 模块划分

```text
toy_vscode_remote_demo/
  DESIGN.md
  README.md
  requirements.txt
  toyremote/
    __init__.py
    client.py
    crypto_utils.py
    protocol.py
    server.py
    workspace.py
```

### 4.1 crypto_utils.py

负责密码学相关能力：

- Base64 编解码
- Ed25519 主机密钥加载和生成
- 主机公钥指纹计算
- X25519 公钥序列化
- Ed25519 签名验证
- HKDF 会话密钥派生
- AES-GCM 加密和解密

### 4.2 protocol.py

负责消息传输格式：

- 4 字节网络序长度前缀
- 明文 JSON 消息
- 加密 JSON 消息
- socket 完整读取
- 最大 frame 大小限制

握手阶段使用明文 JSON，因为此时还没有会话密钥。

认证和业务请求使用加密 JSON。

### 4.3 workspace.py

负责远程工作区能力：

- 限制所有路径必须在 workspace root 内
- 列出目录
- 读取文本文件
- 写入文本文件
- 搜索文本
- 执行 shell 命令

这是本 demo 中最接近 VS Code Remote 文件系统 provider 的部分。

### 4.4 server.py

负责远程 server：

- 监听 TCP 端口
- 服务端 hello
- 用户认证
- 请求循环
- 根据请求类型调用 workspace 能力
- 返回 JSON 响应

### 4.5 client.py

负责本地 client：

- 连接 server
- known hosts 校验
- 用户认证
- 命令行子命令
- 交互式 REPL

## 5. 协议分层

本 demo 协议分为三层：

```text
TCP
  ↓
Toy SSH secure transport
  ↓
Remote workspace RPC
```

### 5.1 TCP 层

使用 Python 标准库 `socket`。

服务端默认监听：

```text
127.0.0.1:2299
```

### 5.2 安全传输层

沿用 Toy SSH 的设计：

```text
server_hello:
  type
  host_key
  host_key_fingerprint
  kex_key
  signature

client_hello:
  type
  kex_key
```

握手完成后，客户端和服务端得到相同的 AES-GCM session key。

后续所有请求都使用加密 JSON。

### 5.3 RPC 层

RPC 请求和响应都是 JSON 对象。

通用响应格式：

```json
{
  "ok": true,
  "result": {}
}
```

错误响应格式：

```json
{
  "ok": false,
  "error": "message"
}
```

## 6. 支持的远程能力

### 6.1 workspace_info

返回远程 workspace 信息：

```json
{
  "type": "workspace_info"
}
```

### 6.2 list_dir

列出远程目录：

```json
{
  "type": "list_dir",
  "path": "."
}
```

### 6.3 read_file

读取远程文本文件：

```json
{
  "type": "read_file",
  "path": "README.md"
}
```

### 6.4 write_file

写入远程文本文件：

```json
{
  "type": "write_file",
  "path": "notes/demo.txt",
  "content": "hello remote"
}
```

### 6.5 search_text

在远程 workspace 中搜索文本：

```json
{
  "type": "search_text",
  "query": "TODO",
  "path": "."
}
```

### 6.6 exec

在远程 workspace 中执行命令：

```json
{
  "type": "exec",
  "command": "python --version"
}
```

### 6.7 close

关闭连接：

```json
{
  "type": "close"
}
```

## 7. 工作区路径安全

远程文件访问必须被限制在 workspace root 内。

例如服务端启动时指定：

```bash
python -m toyremote.server --workspace D:\work\project
```

客户端请求：

```text
../../Windows/System32/config
```

服务端会解析真实路径，然后检查是否仍然位于 workspace root 内。

如果越界，服务端返回错误：

```json
{
  "ok": false,
  "error": "path escapes workspace"
}
```

## 8. 和真实 VS Code Remote 的对应关系

本地 `toyremote.client` 类似真实 VS Code 的 UI client。

远程 `toyremote.server` 类似简化版 VS Code Server。

`workspace.py` 类似远程文件系统 provider。

`exec` 类似远程终端或任务执行。

`search_text` 类似远程搜索服务。

加密传输层类似 Remote - SSH 里的 SSH 通道。

## 9. 主要限制

这个项目是教学 demo，不是生产系统。

主要限制：

- 不兼容真实 VS Code Remote 协议
- 不兼容真实 SSH 协议
- 没有多路复用 channel
- 没有真正的远程终端 PTY
- 没有语言服务 LSP
- 没有调试 DAP
- 没有扩展宿主
- 没有端口转发
- 没有细粒度权限模型
- `exec` 会执行客户端传入的 shell 命令

请只在本机或可信环境中运行。

## 10. 后续可扩展方向

可以继续增加：

- 交互式 PTY 终端
- 多 channel 复用
- 文件 watcher
- 简单 LSP 代理
- Debug Adapter 代理
- 端口转发
- 二进制文件传输
- 用户公钥认证
- 压缩传输
- 多客户端并发
- 远程扩展进程模型

