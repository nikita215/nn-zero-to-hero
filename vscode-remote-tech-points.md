# VS Code Remote 全技术点学习清单

## 1. VS Code Remote 总览

VS Code Remote 是一组让本地 VS Code 连接远程开发环境的能力，核心思想是：

- UI 在本地运行
- 代码、终端、调试、语言服务在远程环境运行
- 本地 VS Code 通过协议与远程 VS Code Server 通信

主要形态：

- Remote - SSH
- Dev Containers
- WSL
- GitHub Codespaces
- Remote Tunnels
- 自建远程开发环境

---

## 2. 核心架构

### 2.1 Client-Server 架构

需要理解：

- VS Code 本地客户端
- VS Code Server
- Extension Host
- Language Server
- Debug Adapter
- File Watcher
- Terminal Server
- 远程文件系统访问
- 本地 UI 与远程计算分离

### 2.2 VS Code Server

技术点：

- VS Code Server 的安装位置
- Server 启动流程
- Server 生命周期管理
- Server 版本与本地 VS Code 版本匹配
- `.vscode-server` 目录结构
- Server 日志
- Server 自动更新
- Server 崩溃排查

常见路径：

```bash
~/.vscode-server
~/.vscode-server-insiders
~/.vscode-remote
```

### 2.3 Extension Host

技术点：

- 本地扩展 vs 远程扩展
- UI Extension
- Workspace Extension
- Extension Kind
- 扩展安装位置
- 扩展同步
- 扩展运行环境差异
- 扩展依赖的系统工具

---

## 3. Remote - SSH

### 3.1 SSH 基础

必须掌握：

- SSH 协议
- OpenSSH
- SSH Client
- SSH Server
- 公钥认证
- 密码认证
- Agent Forwarding
- Port Forwarding
- ProxyJump
- ProxyCommand
- SSH Config

常见文件：

```bash
~/.ssh/config
~/.ssh/id_rsa
~/.ssh/id_ed25519
~/.ssh/known_hosts
~/.ssh/authorized_keys
```

### 3.2 SSH 配置

技术点：

```sshconfig
Host dev-server
    HostName 192.168.1.100
    User ubuntu
    Port 22
    IdentityFile ~/.ssh/id_ed25519
    ForwardAgent yes
```

需要理解：

- Host
- HostName
- User
- Port
- IdentityFile
- ForwardAgent
- ServerAliveInterval
- StrictHostKeyChecking
- LocalForward
- RemoteForward
- DynamicForward

### 3.3 SSH 密钥体系

技术点：

- RSA
- Ed25519
- 私钥
- 公钥
- passphrase
- ssh-agent
- ssh-add
- authorized_keys
- known_hosts
- Host Key Verification

### 3.4 跳板机

技术点：

- Bastion Host
- Jump Host
- ProxyJump
- ProxyCommand
- 多级 SSH
- 内网服务器访问
- 云服务器安全组

示例：

```sshconfig
Host internal
    HostName 10.0.0.10
    User ubuntu
    ProxyJump bastion
```

### 3.5 端口转发

技术点：

- Local Port Forwarding
- Remote Port Forwarding
- Dynamic Port Forwarding
- SOCKS Proxy
- VS Code 自动端口转发
- Web 服务预览
- 远程调试端口暴露

示例：

```bash
ssh -L 8080:localhost:8080 user@server
ssh -R 9000:localhost:3000 user@server
ssh -D 1080 user@server
```

---

## 4. Dev Containers

### 4.1 Docker 基础

必须掌握：

- Docker Engine
- Docker CLI
- Docker Image
- Docker Container
- Dockerfile
- Docker Volume
- Docker Network
- Docker Compose
- Build Context
- Layer Cache
- Multi-stage Build

### 4.2 devcontainer.json

核心文件：

```json
{
  "name": "dev-env",
  "image": "mcr.microsoft.com/devcontainers/typescript-node",
  "features": {},
  "customizations": {
    "vscode": {
      "extensions": []
    }
  }
}
```

技术点：

- `image`
- `build`
- `dockerFile`
- `context`
- `features`
- `customizations`
- `settings`
- `extensions`
- `mounts`
- `workspaceFolder`
- `postCreateCommand`
- `postStartCommand`
- `remoteUser`
- `containerUser`
- `forwardPorts`
- `portsAttributes`

### 4.3 Dockerfile

技术点：

- base image
- package manager
- user permissions
- environment variables
- working directory
- cache optimization
- build arguments
- entrypoint
- CMD

### 4.4 Docker Compose

技术点：

- 多容器开发环境
- 数据库容器
- Redis / MQ / Elasticsearch
- service network
- volume persistence
- depends_on
- environment
- healthcheck

### 4.5 Dev Container Features

技术点：

- 官方 Features
- 自定义 Features
- Feature 安装顺序
- 可复用开发环境
- `ghcr.io/devcontainers/features`

---

## 5. WSL Remote

### 5.1 WSL 基础

技术点：

- WSL 1 vs WSL 2
- Linux Kernel
- Windows 与 Linux 文件系统互通
- WSL 网络模型
- WSL 发行版
- systemd 支持
- Windows Terminal

### 5.2 文件系统

重点理解：

- `/home/user/project`
- `/mnt/c/Users/...`
- Windows 文件系统性能问题
- Linux 文件权限
- 换行符差异
- symlink 差异

### 5.3 WSL 网络

技术点：

- localhost 转发
- NAT 网络
- Windows 访问 WSL 服务
- WSL 访问 Windows 服务
- 防火墙
- DNS 配置

---

## 6. GitHub Codespaces

### 6.1 Codespaces 架构

技术点：

- 云端开发容器
- GitHub 仓库集成
- devcontainer.json
- 预构建 Prebuild
- Machine Type
- Dotfiles
- Secrets
- Port Forwarding

### 6.2 Codespaces 配置

技术点：

- `.devcontainer`
- Repository Secrets
- User Secrets
- Codespaces lifecycle
- Prebuild configuration
- 容器资源限制
- 成本控制

---

## 7. Remote Tunnels

### 7.1 Tunnel 基础

技术点：

- VS Code Tunnel
- Remote Tunnel CLI
- 无公网 IP 远程访问
- 反向连接
- Microsoft / GitHub 账号认证
- HTTPS relay
- Remote machine registration

### 7.2 使用场景

包括：

- 家里电脑远程连接
- 内网服务器远程开发
- 无法配置 SSH 的环境
- 临时远程协作

---

## 8. 文件系统与同步

### 8.1 远程文件访问

技术点：

- Remote File System Provider
- 文件读写 RPC
- 文件监听
- 大文件处理
- 符号链接
- 文件权限
- 文件编码

### 8.2 文件监听

技术点：

- inotify
- fswatch
- polling
- watcher limit
- Linux `fs.inotify.max_user_watches`
- node_modules 监听优化

常见配置：

```bash
sudo sysctl fs.inotify.max_user_watches=524288
```

---

## 9. 终端与 Shell

技术点：

- Integrated Terminal
- Login Shell
- Interactive Shell
- Bash
- Zsh
- Fish
- PowerShell
- 环境变量加载顺序
- PATH 差异
- shell startup scripts

常见文件：

```bash
~/.bashrc
~/.bash_profile
~/.profile
~/.zshrc
/etc/profile
```

---

## 10. 调试系统

### 10.1 VS Code Debug 架构

技术点：

- Debug Adapter Protocol
- Debug Adapter
- launch.json
- attach
- launch
- source map
- breakpoint
- remote path mapping

### 10.2 常见语言调试

需要分别掌握：

- Node.js remote debug
- Python debugpy
- Go dlv
- Java Debug Server
- C/C++ gdb/lldb
- Rust lldb/gdb
- .NET debugger
- Chrome DevTools Protocol

### 10.3 容器调试

技术点：

- attach to container
- debug port forwarding
- path mapping
- source map
- multi-container debug

---

## 11. 语言服务

技术点：

- Language Server Protocol, LSP
- TypeScript Server
- Python Pylance / Pyright
- clangd
- gopls
- rust-analyzer
- Java Language Server
- ESLint server
- Prettier server
- 远程依赖索引
- 代码补全性能
- workspace indexing

---

## 12. 端口与网络

技术点：

- 自动端口检测
- Port Forwarding
- Public Port
- Private Port
- Localhost 映射
- IPv4 / IPv6
- NAT
- Firewall
- Reverse Proxy
- HTTPS
- WebSocket
- CORS
- Cookie domain
- OAuth callback

---

## 13. 身份认证与安全

### 13.1 SSH 安全

技术点：

- 密钥权限
- 禁止密码登录
- 禁止 root 登录
- Fail2ban
- SSH Agent Forwarding 风险
- known_hosts 校验
- Host Key Rotation

### 13.2 容器安全

技术点：

- rootless container
- container user
- Docker socket 风险
- privileged container
- capabilities
- seccomp
- AppArmor
- volume mount 风险
- secret 注入

### 13.3 Codespaces 安全

技术点：

- GitHub Token
- Repository Permission
- Secret Scope
- Port Visibility
- Organization Policy

---

## 14. 性能优化

技术点：

- 网络延迟
- 文件系统性能
- 扩展性能
- 大仓库优化
- watcher 排除
- search.exclude
- files.watcherExclude
- node_modules 优化
- Docker volume 性能
- WSL 文件位置优化
- Server 资源限制
- CPU / RAM / IO 监控

常见配置：

```json
{
  "files.watcherExclude": {
    "**/node_modules/**": true,
    "**/.git/**": true
  },
  "search.exclude": {
    "**/node_modules": true,
    "**/dist": true
  }
}
```

---

## 15. 日志与排障

### 15.1 VS Code 日志

技术点：

- Remote-SSH Log
- Window Log
- Extension Host Log
- Server Log
- Terminal Log
- Developer Tools Console

### 15.2 常见问题

需要掌握：

- SSH 连接失败
- Server 安装失败
- 权限错误
- 扩展无法运行
- 端口转发失败
- 终端环境变量不对
- 文件监听失效
- Docker build 失败
- WSL 网络异常
- Git 权限异常

### 15.3 常用诊断命令

```bash
ssh -vvv user@host
ps aux | grep vscode
netstat -tulpn
ss -tulpn
lsof -i :3000
df -h
free -h
top
htop
journalctl -xe
docker ps
docker logs
docker inspect
```

---

## 16. Git 与远程开发

技术点：

- Git over SSH
- Git credential helper
- GitHub SSH key
- GPG signing
- commit signing in remote
- credential forwarding
- Git LFS
- submodule
- sparse checkout
- worktree
- line ending
- file permission

---

## 17. 云服务器基础

技术点：

- Linux Server
- Ubuntu / Debian / CentOS
- 用户管理
- sudo
- systemd
- firewall
- ufw
- security group
- cloud-init
- disk mount
- swap
- package manager
- SSH hardening

云厂商相关：

- AWS EC2
- Azure VM
- Google Compute Engine
- 阿里云 ECS
- 腾讯云 CVM
- 华为云 ECS

---

## 18. Linux 基础能力

必须掌握：

- 文件权限
- 用户与用户组
- 进程管理
- systemd
- 网络命令
- 包管理
- shell scripting
- 环境变量
- crontab
- 日志系统
- 磁盘管理

常用命令：

```bash
ls
cd
pwd
chmod
chown
ps
kill
top
df
du
ip
ss
curl
wget
tar
systemctl
journalctl
```

---

## 19. Windows 相关技术

技术点：

- OpenSSH Client on Windows
- Windows Credential Manager
- PowerShell
- Windows Terminal
- WSL
- Hyper-V
- Docker Desktop
- 文件路径差异
- CRLF / LF
- 防火墙
- 代理设置
- 证书信任

---

## 20. 代理与企业网络

技术点：

- HTTP Proxy
- HTTPS Proxy
- SOCKS Proxy
- PAC
- NO_PROXY
- 公司 CA 证书
- TLS inspection
- npm / pip / git proxy
- Docker proxy
- VS Code proxy
- SSH over Proxy

常见环境变量：

```bash
HTTP_PROXY
HTTPS_PROXY
NO_PROXY
http_proxy
https_proxy
no_proxy
```

---

## 21. 包管理器与开发工具链

需要按语言掌握：

### JavaScript / TypeScript

- Node.js
- npm
- pnpm
- yarn
- nvm
- corepack
- TypeScript
- ESLint
- Prettier
- Vite / Webpack / Next.js

### Python

- Python
- pyenv
- venv
- virtualenv
- pip
- pipx
- poetry
- uv
- conda
- debugpy
- pytest

### Go

- Go toolchain
- GOPATH
- GOMODCACHE
- gopls
- dlv

### Rust

- rustup
- cargo
- rust-analyzer
- clippy
- lldb

### Java

- JDK
- Maven
- Gradle
- jdtls

### C / C++

- gcc
- clang
- make
- cmake
- gdb
- lldb
- clangd

---

## 22. 配置文件体系

需要理解：

```text
.vscode/settings.json
.vscode/launch.json
.vscode/tasks.json
.vscode/extensions.json
.devcontainer/devcontainer.json
.devcontainer/Dockerfile
.devcontainer/docker-compose.yml
.ssh/config
.gitconfig
.editorconfig
```

重点：

- 用户配置
- 工作区配置
- 远程配置
- 容器配置
- 项目配置
- 配置优先级

---

## 23. 自动化任务

技术点：

- VS Code Tasks
- `tasks.json`
- preLaunchTask
- problemMatcher
- shell task
- process task
- background task
- Dev Container lifecycle commands
- postCreateCommand
- postStartCommand
- CI 与本地开发一致性

---

## 24. Remote 开发工作流

典型流程：

1. 本地安装 VS Code
2. 安装 Remote 扩展
3. 准备远程机器或容器
4. 配置 SSH / WSL / Dev Container
5. 打开远程工作区
6. 安装远程扩展
7. 配置终端、调试、端口转发
8. 开发、测试、调试
9. Git 提交与推送
10. 排查性能与环境问题

---

## 25. 推荐学习顺序

### 第一阶段：基础

- Linux 基础
- SSH 基础
- Git 基础
- VS Code 基础配置

### 第二阶段：Remote - SSH

- SSH Config
- 密钥认证
- VS Code Server
- 远程终端
- 端口转发
- 日志排查

### 第三阶段：Dev Containers

- Docker
- Dockerfile
- Docker Compose
- devcontainer.json
- 容器调试

### 第四阶段：WSL

- WSL 2
- Linux 文件系统
- Windows 与 Linux 互操作
- Docker Desktop + WSL

### 第五阶段：高级能力

- LSP
- DAP
- 扩展运行机制
- 代理与企业网络
- 安全加固
- 性能优化

### 第六阶段：云端开发

- Codespaces
- Remote Tunnels
- 云服务器
- 团队开发环境标准化

---

## 26. 最终能力目标

学完后应该能够：

- 独立配置 Remote - SSH 开发环境
- 理解 VS Code 本地与远程的分工
- 排查 VS Code Server 安装和连接问题
- 使用 Dev Container 固化团队开发环境
- 在 WSL 中高效开发
- 配置远程调试和端口转发
- 优化远程大项目性能
- 处理代理、证书、权限、网络问题
- 设计安全、可复现、可迁移的远程开发环境
