# Toy SSH Demo

这是一个用 Python 实现的“教学版 SSH”demo，用来帮助理解 SSH 的核心机制：

- TCP client/server
- 服务端主机密钥与指纹校验
- 临时密钥交换
- 会话密钥派生
- 加密消息通道
- 用户认证
- 远程命令执行

它不是 OpenSSH 协议的完整实现，不能替代真正的 `ssh`。这个工程只适合本地学习协议原理。

## 1. 工程结构

```text
toy_ssh_demo/
  README.md
  requirements.txt
  toyssh/
    __init__.py
    client.py
    crypto_utils.py
    protocol.py
    server.py
```

## 2. 安装依赖

```bash
cd toy_ssh_demo
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Linux/macOS 激活虚拟环境：

```bash
source .venv/bin/activate
```

## 3. 启动服务端

默认监听 `127.0.0.1:2222`，用户名和密码都是 `demo`。

```bash
python -m toyssh.server
```

第一次启动时，服务端会自动生成一个 Ed25519 主机私钥：

```text
config/host_ed25519.key
```

## 4. 客户端连接并执行命令

第一次连接需要信任服务端主机指纹：

```bash
python -m toyssh.client 127.0.0.1 --trust-on-first-use --command "whoami"
```

再次连接时可以不加 `--trust-on-first-use`：

```bash
python -m toyssh.client 127.0.0.1 --command "whoami"
```

Windows 下也可以试：

```bash
python -m toyssh.client 127.0.0.1 --command "dir"
```

Linux/macOS 下可以试：

```bash
python -m toyssh.client 127.0.0.1 --command "ls -la"
```

## 5. 这个 demo 模拟了 SSH 的哪些部分

### 5.1 主机身份验证

服务端有一把长期 Ed25519 主机密钥。客户端第一次连接时会保存服务端公钥指纹到：

```text
.toyssh_known_hosts.json
```

以后再次连接时，如果服务端指纹变化，客户端会拒绝连接。

这模拟了真实 SSH 的：

```text
~/.ssh/known_hosts
```

### 5.2 密钥交换

每次连接时，服务端和客户端都会各自生成一对临时 X25519 密钥。

双方交换临时公钥后，可以计算出同一个共享秘密：

```text
client_private + server_public -> shared_secret
server_private + client_public -> shared_secret
```

这个共享秘密不会直接作为加密密钥，而是经过 HKDF 派生出 AES-GCM 会话密钥。

### 5.3 加密通道

握手完成后，认证请求、命令请求、命令输出都会通过 AES-GCM 加密传输。

消息结构大致是：

```text
4 字节长度
nonce + ciphertext
```

### 5.4 用户认证

客户端在加密通道内发送：

```json
{
  "type": "auth",
  "username": "demo",
  "password": "demo"
}
```

服务端验证通过后，才允许执行命令。

真实 SSH 支持更复杂的认证方式，比如公钥认证、keyboard-interactive、GSSAPI 等。

### 5.5 远程命令执行

客户端发送命令：

```json
{
  "type": "exec",
  "command": "whoami"
}
```

服务端使用 `subprocess.run()` 在服务端机器执行命令，然后把：

- stdout
- stderr
- exit code

通过加密通道返回客户端。

## 6. 协议流程

```text
Client                              Server
  |                                    |
  | -------- TCP connect ------------> |
  |                                    |
  | <---- server hello ----------------|
  |       host public key              |
  |       server ephemeral key         |
  |       signature                    |
  |                                    |
  | verify host signature              |
  | check known_hosts fingerprint      |
  |                                    |
  | ---- client ephemeral key -------->|
  |                                    |
  | both derive AES-GCM session key    |
  |                                    |
  | ---- encrypted auth request ------>|
  | <--- encrypted auth response ------|
  |                                    |
  | ---- encrypted exec request ------>|
  | <--- encrypted exec result --------|
  |                                    |
```

## 7. 安全说明

这个项目是学习 demo，不是生产级 SSH。

主要限制：

- 没有实现完整 SSH wire protocol
- 没有实现多 channel
- 没有实现交互式 shell
- 没有实现公钥用户登录
- 没有完善的权限隔离
- 服务端会执行客户端传来的 shell 命令

请只在本机或可信环境中运行。

## 8. 和真实 SSH 的对应关系

| 真实 SSH | 本 demo |
| --- | --- |
| SSH transport layer | TCP + framing + AES-GCM |
| host key | Ed25519 host key |
| known_hosts | `.toyssh_known_hosts.json` |
| key exchange | X25519 |
| session key | HKDF-SHA256 derived AES key |
| userauth | encrypted username/password |
| exec channel | encrypted `exec` request |
| stdout/stderr/exit code | encrypted JSON result |

