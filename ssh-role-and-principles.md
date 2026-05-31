# SSH 的作用、原理与功能实现

## 1. SSH 的作用

SSH，全称是 **Secure Shell**，主要作用是：**让你安全地远程登录另一台机器，并在那台机器上执行命令、传输文件、转发端口**。

在 VS Code Remote - SSH 里，SSH 的作用是：

1. 建立本地 VS Code 到远程服务器的安全连接
2. 在远程服务器上安装并启动 VS Code Server
3. 把本地编辑器 UI 和远程代码环境连接起来
4. 让终端、文件读写、调试、端口转发都通过加密通道进行

简单说：

```text
本地 VS Code
   |
   |  SSH 加密连接
   v
远程服务器
   |
   v
VS Code Server / 项目代码 / 终端 / 调试环境
```

## 2. SSH 能做什么

### 2.1 远程登录

你可以从本机登录远程服务器：

```bash
ssh user@server_ip
```

登录后，你看到的是远程机器的 shell，可以执行：

```bash
ls
cd
python train.py
git pull
docker ps
```

这些命令都在远程服务器上运行。

### 2.2 安全传输文件

SSH 也可以用来传文件，比如：

```bash
scp local.txt user@server:/home/user/
```

或者用：

```bash
sftp user@server
```

底层仍然依赖 SSH 的加密通信能力。

### 2.3 端口转发

SSH 可以把远程机器上的服务映射到本地。

比如远程服务器上运行了一个 Web 服务：

```text
远程服务器 localhost:8000
```

你可以用：

```bash
ssh -L 8000:localhost:8000 user@server
```

然后在本地浏览器访问：

```text
http://localhost:8000
```

实际上访问的是远程服务器上的服务。

这就是 VS Code Remote 里“端口转发”的基础。

### 2.4 作为 VS Code Remote 的连接通道

当你用 VS Code Remote - SSH 连接服务器时，大致过程是：

```text
本地 VS Code
  -> 调用本机 ssh 命令
  -> 登录远程服务器
  -> 检查远程是否有 VS Code Server
  -> 没有则自动下载安装
  -> 启动 VS Code Server
  -> 本地 VS Code 通过 SSH 通道与 Server 通信
```

## 3. SSH 的核心原理

SSH 的核心目标是解决三个问题：

1. 我连接的真的是目标服务器吗？
2. 服务器怎么确认我是合法用户？
3. 通信内容如何防止被窃听或篡改？

对应的机制是：

```text
服务器身份验证
用户身份认证
加密通信
```

## 4. 服务器身份验证

第一次连接服务器时，你可能会看到：

```text
The authenticity of host '1.2.3.4' can't be established.
Are you sure you want to continue connecting?
```

这是 SSH 在告诉你：

> 我还不认识这台服务器，要不要信任它？

如果你输入 `yes`，本机会把服务器的公钥指纹保存到：

```bash
~/.ssh/known_hosts
```

以后再连接时，SSH 会检查：

```text
当前服务器公钥 == known_hosts 里记录的公钥
```

如果不一致，就会报警：

```text
WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED
```

这可以防止中间人攻击。

## 5. 用户身份认证

SSH 常见认证方式有两种：密码认证和密钥认证。

### 5.1 密码认证

```bash
ssh user@server
```

然后输入用户密码。

特点：

- 简单
- 但容易被暴力破解
- 不适合长期暴露在公网的服务器

### 5.2 密钥认证

更推荐使用密钥认证。

你本地有一对密钥：

```text
私钥：保存在本地，不能泄露
公钥：放到远程服务器
```

常见文件：

```bash
~/.ssh/id_ed25519        # 私钥
~/.ssh/id_ed25519.pub    # 公钥
```

远程服务器保存你的公钥：

```bash
~/.ssh/authorized_keys
```

连接时，不是把私钥发给服务器，而是：

```text
1. 客户端告诉服务器：我要用这个公钥对应的身份登录
2. 服务器生成一个随机 challenge
3. 客户端用私钥对 challenge 签名
4. 服务器用公钥验证签名
5. 验证通过，允许登录
```

关键点：

> 私钥永远不会离开本机。

## 6. 加密通信

SSH 连接建立后，双方会协商一个临时会话密钥。

之后所有通信都会被加密：

```text
命令输入
命令输出
文件传输
端口转发
VS Code Server 通信
```

都会走这个加密通道。

大致过程：

```text
客户端与服务器建立 TCP 连接
        |
        v
协商加密算法
        |
        v
验证服务器身份
        |
        v
用户认证
        |
        v
生成会话密钥
        |
        v
开始加密通信
```

## 7. SSH 相关文件

### 7.1 本地客户端

```bash
~/.ssh/config
```

保存 SSH 连接配置。

```bash
~/.ssh/id_ed25519
```

私钥。

```bash
~/.ssh/id_ed25519.pub
```

公钥。

```bash
~/.ssh/known_hosts
```

保存你信任过的服务器指纹。

### 7.2 远程服务器

```bash
~/.ssh/authorized_keys
```

保存允许登录这个用户的公钥。

```bash
/etc/ssh/sshd_config
```

SSH 服务端配置。

## 8. SSH 在 VS Code Remote 中的完整流程

假设你在 VS Code 中连接：

```text
user@my-server
```

流程大致是：

```text
1. VS Code 调用本机 ssh
2. ssh 根据 ~/.ssh/config 找到服务器地址、用户名、端口、密钥
3. 建立 TCP 连接到远程 22 端口
4. 验证服务器 host key
5. 使用密码或密钥完成用户认证
6. 登录远程 shell
7. VS Code 在远程创建 ~/.vscode-server
8. 下载并启动 VS Code Server
9. 本地 VS Code 与远程 VS Code Server 建立通信
10. 文件、终端、调试、端口转发都通过 SSH 通道工作
```

## 9. SSH 的功能是怎么实现的

SSH 的这些功能，本质上都是建立在同一个东西上：**一条安全的双向加密通道**。

也就是说，SSH 不是每个功能都重新发明一套协议，而是先建立安全连接，然后在这条连接里承载不同类型的数据流。

可以理解成：

```text
TCP 连接
  ↓
SSH 加密连接
  ↓
多个逻辑通道 channel
  ↓
登录 / 命令执行 / 文件传输 / 端口转发 / VS Code Remote
```

## 10. SSH 如何建立加密连接

当你执行：

```bash
ssh user@server
```

客户端会先连接远程服务器的 SSH 服务，一般是：

```text
server:22
```

底层是普通 TCP：

```text
本地电脑  ->  TCP  ->  远程服务器 22 端口
```

然后 SSH 在这个 TCP 连接上做几件事：

1. 双方交换支持的 SSH 版本
2. 协商加密算法
3. 通过密钥交换生成会话密钥
4. 验证服务器身份
5. 验证用户身份
6. 开始加密传输

建立完成后，后面的内容都被加密。

```text
你输入的命令
服务器返回的输出
传输的文件内容
转发的 HTTP 请求
VS Code Remote 通信数据
```

都会放进这条加密连接里。

## 11. SSH 如何实现远程登录

远程登录其实就是：

> SSH 客户端请求服务器给你分配一个远程 shell。

过程大致是：

```text
客户端：我要登录
服务器：认证通过，给你创建一个 shell
服务器：启动 /bin/bash 或 /bin/zsh
客户端：把你的键盘输入发过去
服务器：把 shell 输出发回来
```

更具体一点：

```text
本地键盘输入
  ↓
SSH 客户端加密
  ↓
网络传输
  ↓
SSH 服务端解密
  ↓
写入远程 shell 的 stdin
  ↓
shell 执行命令
  ↓
stdout / stderr 输出
  ↓
SSH 服务端加密返回
  ↓
本地 SSH 客户端解密显示
```

所以你看到的终端，其实是远程 shell 的输入输出被搬到了本地。

## 12. SSH 如何执行单条命令

比如：

```bash
ssh user@server "ls -lh"
```

这和登录类似，只是服务器不启动交互式 shell，而是直接启动一个进程：

```text
远程服务器执行：ls -lh
```

然后 SSH 把这个进程的：

```text
stdin
stdout
stderr
exit code
```

转回本地。

所以本质是：

```text
本地发起命令请求
远程创建进程
远程执行命令
把输出和退出码传回本地
```

## 13. SSH 如何实现密钥登录

密钥登录依赖的是**非对称加密签名**。

你有一对密钥：

```text
私钥：本地保存，不能泄露
公钥：放到服务器 ~/.ssh/authorized_keys
```

登录时不是把私钥发过去，而是：

```text
服务器：我这里有你的公钥
服务器：生成一个随机 challenge
客户端：用私钥对 challenge 签名
服务器：用公钥验证签名
```

如果验证通过，说明：

```text
这个客户端确实持有对应私钥
```

于是允许登录。

关键点：

> 私钥始终不离开你的电脑。

这就是 SSH 密钥登录安全的原因。

## 14. SSH 如何实现文件传输

文件传输也是走 SSH 加密通道。

常见有两种方式：

```text
scp
sftp
```

### 14.1 scp

早期 `scp` 的思想比较简单：

```text
本地 scp
  ↓
通过 SSH 在远程启动 scp 程序
  ↓
双方通过 stdin/stdout 传文件内容和元数据
```

比如：

```bash
scp a.txt user@server:/tmp/
```

大致相当于：

```text
本地读取 a.txt
通过 SSH 发送文件名、权限、大小、内容
远程 scp 接收并写入 /tmp/a.txt
```

### 14.2 sftp

`sftp` 更像一个专门的文件操作协议。

它通过 SSH 启动远程的 SFTP 子系统：

```text
客户端：我要打开文件
服务器：打开成功
客户端：我要读取第 0-32768 字节
服务器：返回数据
客户端：我要写入这些字节
服务器：写入成功
```

所以 SFTP 支持：

```text
列目录
上传
下载
删除
重命名
修改权限
```

这些都是通过 SSH channel 发请求实现的。

## 15. SSH 如何实现端口转发

端口转发是 SSH 最经典的能力之一。

核心思路是：

> 本地监听一个端口，把收到的数据通过 SSH 加密通道转给远程某个地址。

例如：

```bash
ssh -L 8080:localhost:3000 user@server
```

意思是：

```text
本地 8080
  ↓
SSH 加密通道
  ↓
远程服务器访问 localhost:3000
```

当你本地浏览器访问：

```text
http://localhost:8080
```

实际流程是：

```text
浏览器请求 localhost:8080
  ↓
本地 SSH 客户端收到连接
  ↓
SSH 客户端把 HTTP 数据打包进 SSH channel
  ↓
远程 SSH 服务端解包
  ↓
远程 SSH 服务端连接 localhost:3000
  ↓
远程服务返回响应
  ↓
响应通过 SSH channel 回到本地
  ↓
浏览器收到响应
```

所以浏览器以为自己在访问本地 8080，但真正访问的是远程服务器的 3000。

## 16. SSH 如何实现反向端口转发

比如：

```bash
ssh -R 9000:localhost:3000 user@server
```

意思是：

```text
远程服务器监听 9000
  ↓
通过 SSH 通道
  ↓
访问本地电脑的 localhost:3000
```

流程是反过来的：

```text
别人访问远程 server:9000
  ↓
远程 SSH 服务端收到连接
  ↓
通过 SSH channel 发回本地
  ↓
本地 SSH 客户端连接 localhost:3000
  ↓
本地服务响应
  ↓
响应再通过 SSH 返回远程访问者
```

这常用于：

```text
把本地开发服务临时暴露给远程机器
内网穿透
Webhook 测试
```

## 17. SSH 如何实现动态代理

比如：

```bash
ssh -D 1080 user@server
```

这会在本地创建一个 SOCKS 代理：

```text
本地 1080 是 SOCKS 代理端口
```

浏览器或应用把请求发给：

```text
localhost:1080
```

SSH 客户端收到后，根据 SOCKS 协议知道你想访问哪个目标网站，然后让远程服务器代你访问。

流程：

```text
浏览器 -> localhost:1080
SSH 客户端解析目标地址
SSH 通道发送请求
远程 SSH 服务端连接目标网站
目标网站响应
响应通过 SSH 返回浏览器
```

所以它可以实现：

```text
代理访问
内网访问
绕过本地网络限制
```

## 18. SSH 如何支撑 VS Code Remote

VS Code Remote - SSH 本质上组合了前面的能力。

当你连接远程机器时，VS Code 会做：

```text
1. 调用本地 ssh
2. 登录远程服务器
3. 在远程服务器创建目录 ~/.vscode-server
4. 上传或下载 VS Code Server
5. 启动远程 VS Code Server
6. 建立本地 VS Code 与远程 Server 的通信
7. 用 SSH 隧道承载后续数据
```

之后这些功能都发生在远程：

```text
文件读取
终端
Git
扩展
语言服务
调试
测试
```

本地 VS Code 主要负责：

```text
显示 UI
接收键盘鼠标
渲染编辑器
显示结果
```

远程 VS Code Server 负责：

```text
访问远程文件
运行扩展
启动终端
执行搜索
运行语言服务
启动调试器
```

通信方式大致是：

```text
本地 VS Code UI
  ↓
SSH 通道
  ↓
远程 VS Code Server
  ↓
远程项目 / 终端 / 语言服务 / 调试器
```

## 19. 为什么 SSH 可以同时做这么多事

因为 SSH 连接里有一个概念叫 **channel**。

一条 SSH 连接里可以开多个逻辑通道：

```text
SSH Connection
  ├── channel 1: shell
  ├── channel 2: 文件传输
  ├── channel 3: 端口转发
  ├── channel 4: VS Code Server 通信
  └── channel 5: 远程命令
```

它们共享同一条加密连接，但逻辑上互不干扰。

这就像一条高速公路上有多条车道：

```text
车道 A 运命令输入输出
车道 B 运文件内容
车道 C 运 HTTP 请求
车道 D 运 VS Code 数据
```

## 20. 一句话总结

SSH 的本质是：

> 通过身份验证和加密通道，让你安全地控制远程机器。

它的实现原理是：

> 先用密钥交换和身份认证建立一条安全加密连接，然后在这条连接上创建多个 channel，用不同的 channel 承载远程 shell、命令执行、文件传输、端口转发和 VS Code Remote 通信。

所以 SSH 看起来功能很多，但底层核心其实就是：

```text
加密连接 + 身份认证 + 多路复用 channel
```
