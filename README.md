# Browser Stream (Python Edition)

基于 WebRTC 的服务端无头浏览器流媒体应用。

## 功能特性

- 通过 Playwright 控制无头 Chrome 浏览器
- 基于 WebRTC 的屏幕流媒体传输
- 通过 REST API 控制浏览器导航和执行 JavaScript

## 技术栈

- **Playwright** - 浏览器自动化
- **aiohttp** - HTTP/WebSocket 服务器
- **aiortc** - WebRTC 端连接
- **PyAV** - 视频编码/解码

## 安装

### macOS

#### 方式一：使用 Conda（推荐）

```bash
# 安装 Miniforge（Apple Silicon 版）
brew install --cask miniforge

# 初始化 conda
eval "$(~/miniforge3/bin/conda shell.bash hook)"

# 创建 Python 3.11 环境
conda create -n pixel-streaming python=3.11 -y

# 激活环境
conda activate pixel-streaming

# 安装 ffmpeg（PyAV 依赖）
conda install -y ffmpeg

# 安装 Python 依赖
~/miniforge3/envs/pixel-streaming/bin/pip install aiohttp playwright aiortc numpy

# 安装 Playwright 浏览器
~/miniforge3/envs/pixel-streaming/bin/playwright install chromium
```

#### 方式二：使用系统 Python

```bash
# 安装编译工具（如需要）
xcode-select --install

# 安装 ffmpeg
brew install ffmpeg pkg-config cython

# 安装 Python 依赖
/usr/bin/python3 -m pip install --upgrade pip
/usr/bin/python3 -m pip install aiohttp playwright aiortc numpy

# 安装 Playwright 浏览器
python3 -m playwright install chromium
```

### Windows

#### 方式一：使用 Conda（推荐）

```powershell
# 从 https://docs.conda.io/en/latest/miniconda.html 安装 Miniconda

# 创建 Python 3.11 环境
conda create -n pixel-streaming python=3.11 -y

# 激活环境
conda activate pixel-streaming

# 安装 ffmpeg
conda install -y ffmpeg

# 安装 Python 依赖
pip install aiohttp playwright aiortc numpy

# 安装 Playwright 浏览器
playwright install chromium
```

#### 方式二：使用 WSL2（推荐，兼容性更好）

```bash
# 从 Microsoft Store 安装 WSL2 Ubuntu

# 在 WSL2 终端中执行：
sudo apt update
sudo apt install python3.11 python3-pip ffmpeg

pip install aiohttp playwright aiortc numpy
playwright install chromium
```

#### 方式三：原生 Windows

```powershell
# 从 https://www.python.org/downloads/ 安装 Python 3.11

# 安装 Visual Studio Build Tools（PyAV 编译需要）
# 下载地址：https://visualstudio.microsoft.com/visual-cpp-build-tools/

# 使用 Chocolatey 安装 ffmpeg（可选）
choco install ffmpeg

# 安装 Python 依赖
pip install aiohttp playwright aiortc numpy

# 安装 Playwright 浏览器
playwright install chromium
```

### Linux

#### 方式一：使用 apt（Ubuntu/Debian）

```bash
# 安装依赖
sudo apt update
sudo apt install python3.11 python3-pip ffmpeg

# 安装 Python 依赖
pip install aiohttp playwright aiortc numpy

# 安装 Playwright 浏览器
playwright install chromium
```

#### 方式二：使用 Conda

```bash
# 安装 Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# 创建环境
conda create -n pixel-streaming python=3.11 -y
conda activate pixel-streaming

# 安装 ffmpeg
conda install -y ffmpeg

# 安装 Python 依赖
pip install aiohttp playwright aiortc numpy

# 安装 Playwright 浏览器
playwright install chromium
```

### 快速开始

```bash
# macOS 激活 conda 环境
eval "$(~/miniforge3/bin/conda shell.bash hook)"
conda activate pixel-streaming

# Linux/Windows 激活 conda 环境
conda activate pixel-streaming

# 启动服务器
python run.py
```

在浏览器中打开 http://localhost:8080

## 配置

所有配置通过 `config.ini` 文件管理，无需使用环境变量。

### 配置文件 (`config.ini`)

```ini
[server]
host = 0.0.0.0          # 监听所有网络接口
port = 8080              # HTTP 服务端口

[settings]
viewport_width = 1920    # 远程浏览器视口宽度
viewport_height = 1080    # 远程浏览器视口高度
screenshot_quality = 80   # 截图质量 1-100

[turn]
server =                 # TURN 服务器 IP (留空则不使用)
port = 19303            # TURN 端口
user =                   # TURN 用户名
password =               # TURN 密码
```

### 配置项说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `server.host` | 服务监听地址 | `0.0.0.0` |
| `server.port` | 服务端口 | `8080` |
| `settings.viewport_width` | 远程浏览器视口宽度 | `1920` |
| `settings.viewport_height` | 远程浏览器视口高度 | `1080` |
| `settings.screenshot_quality` | 截图 JPEG 质量 | `80` |
| `turn.server` | TURN 服务器 IP | （空） |
| `turn.port` | TURN 端口 | `19303` |
| `turn.user` | TURN 用户名 | （空） |
| `turn.password` | TURN 密码 | （空） |

### 启动应用

```bash
python run.py
```

程序会自动加载 `config.ini` 中的配置。

### 验证配置

```bash
python -c "from app.config import Config; print(Config.get_ice_servers())"
```

### 前端配置 (`web/public/index.html`)

前端会自动使用服务端的 TURN 配置，无需手动配置。

### 部署场景

| 场景 | 配置 |
|------|------|
| 本机测试 | 不配置 `[turn]` |
| 内网互联 | 不配置 `[turn]` |
| 外网部署 | 填写 `[turn]` 配置 |

### 使用 coturn TURN 服务器

本项目使用 coturn 作为 TURN 服务器。配置文件位于 `PixelStreamingInfrastructure/SignallingWebServer/turnserver.conf`。

#### coturn 安装

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install coturn
```

**CentOS/RHEL:**
```bash
sudo yum install coturn
```

**macOS:**
```bash
brew install coturn
```

#### 启动 coturn

**方式一：使用项目配置文件**

```bash
# 复制配置文件到系统目录
sudo cp PixelStreamingInfrastructure/SignallingWebServer/turnserver.conf /etc/coturn/turnserver.conf

# 启动 coturn
sudo systemctl enable coturn
sudo systemctl start coturn

# 查看状态
sudo systemctl status coturn
```

**方式二：命令行启动（调试模式）**

```bash
sudo turnserver -c PixelStreamingInfrastructure/SignallingWebServer/turnserver.conf -v -v -v -f
```

#### 配置文件说明

`turnserver.conf` 配置项详解：

| 配置项 | 说明 | 示例值 |
|--------|------|--------|
| `realm` | TURN 服务器领域名称，用于认证 | `PixelStreaming` |
| `fingerprint` | 在 STUN/TURN 响应中添加指纹 | （无需值） |
| `listening-port` | UDP 监听端口 | `19303` |
| `listening-ip` | 监听 IP地址 | `0.0.0.0` |
| `relay-ip` | 中继 IP地址（分配给客户端的公网地址） | `107.173.83.242` |
| `external-ip` | 外部/公网 IP | `107.173.83.242` |
| `user` | 长期凭证认证的用户名和密码 | `admin:hxkj2026` |
| `tls-listening-port` | TLS 监听端口 | `5349` |
| `lt-cred-mech` | 启用长期凭证认证机制 | （无需值） |
| `min-port` | 中继端口范围起始 | `49152` |
| `max-port` | 中继端口范围结束 | `65535` |
| `no-loopback-peers` | 禁止回环地址作为对等端 | （无需值） |
| `no-self-check` | 禁用自身检查 | （无需值） |
| `verbose` | 详细日志输出 | （无需值） |

#### 关键配置说明

1. **`lt-cred-mech`** - 长期凭证认证，客户端需要提供 username 和 password
2. **`relay-ip`** - TURN 服务器分配给客户端的中继地址，必须是公网可达的 IP
3. **`external-ip`** - 服务器的公网 IP，某些云环境需要显式指定
4. **端口范围** - `min-port` 到 `max-port` 之间的端口用于 TURN 中继连接

#### 防火墙配置

确保云服务器安全组/防火墙开放以下端口：

| 协议 | 端口范围 | 说明 |
|------|----------|------|
| UDP | `listening-port` (19303) | coturn 监听端口 |
| UDP | `min-port` - `max-port` (49152-65535) | TURN 中继端口 |

**Ubuntu/Debian (ufw):**
```bash
sudo ufw allow 19303/udp
sudo ufw allow 49152:65535/udp
```

**云服务器：** 在云控制台的安全组规则中添加上述 UDP 端口。

### 使用 UE5 TURN 服务

UE5 内置 coturn TURN 服务器，默认端口 **19303**。

参考上方 coturn 配置章节启动 TURN 服务后，在 `config.ini` 中填写：

```ini
[turn]
server = 服务器IP
port = 19303
user = your_username
password = your_password
```

## 项目结构

```
pixel_streaming/
├── app/
│   ├── __init__.py
│   ├── config.py          # 配置加载模块
│   ├── main.py            # 服务器入口
│   ├── browser/          # 浏览器管理
│   │   └── manager.py
│   ├── handlers/          # HTTP/WebSocket 处理器
│   │   ├── http.py
│   │   ├── input.py
│   │   └── websocket.py
│   └── webrtc/            # WebRTC 端连接
│       └── peer.py
├── web/
│   └── public/            # 前端文件
├── config.ini              # 配置文件 (所有配置项)
├── requirements.txt
└── run.py

