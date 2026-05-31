# Toy VS Code Remote Demo

这是一个 Python 实现的教学版 VS Code Remote。

它基于前面的 Toy SSH 思路，实现一个加密的远程工作区 RPC 系统，用来理解 VS Code Remote 的基本架构。

## 1. 功能

- 服务端主机指纹校验
- X25519 临时密钥交换
- AES-GCM 加密通道
- 用户名密码认证
- 远程目录列表
- 远程文件读取
- 远程文件写入
- 远程文本搜索
- 远程命令执行
- 本地交互式 REPL

## 2. 安装

```bash
cd toy_vscode_remote_demo
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Linux/macOS：

```bash
source .venv/bin/activate
```

## 3. 启动远程 server

在一个终端中启动：

```bash
python -m toyremote.server --workspace .
```

默认参数：

- host: `127.0.0.1`
- port: `2299`
- username: `demo`
- password: `demo`

你也可以显式指定：

```bash
python -m toyremote.server --host 127.0.0.1 --port 2299 --workspace . --username demo --password demo
```

## 4. 使用客户端

第一次连接需要信任主机指纹：

```bash
python -m toyremote.client 127.0.0.1 --trust-on-first-use info
```

之后可以执行：

```bash
python -m toyremote.client 127.0.0.1 ls .
python -m toyremote.client 127.0.0.1 read README.md
python -m toyremote.client 127.0.0.1 search TODO .
python -m toyremote.client 127.0.0.1 exec "python --version"
```

写入远程文件：

```bash
python -m toyremote.client 127.0.0.1 write notes/hello.txt --text "hello remote"
```

从本地文件写入远程：

```bash
python -m toyremote.client 127.0.0.1 write notes/copy.txt --from-file local.txt
```

## 5. REPL 模式

```bash
python -m toyremote.client 127.0.0.1 --trust-on-first-use repl
```

可用命令：

```text
info
ls [path]
read <path>
write <path> <text>
search <query> [path]
exec <command>
help
exit
```

示例：

```text
remote> info
remote> ls .
remote> read README.md
remote> search import toyremote
remote> exec dir
remote> exit
```

## 6. 设计文档

见：

```text
DESIGN.md
```

## 7. 安全提醒

这是教学 demo，不是生产工具。

服务端的 `exec` 会执行客户端传入的 shell 命令。请只在本机或可信环境中运行。

