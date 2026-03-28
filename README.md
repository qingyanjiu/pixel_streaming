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

### 服务端配置 (`app/config.py`)

```python
class Config:
    HOST = "0.0.0.0"      # 服务监听地址
    PORT = 8080            # 服务端口

    # ICE 服务器配置
    ICE_SERVERS = [
        {"urls": "stun:stun.l.google.com:19302"},
    ]

    # TURN 配置（外网部署时使用）
    # TURN_SERVER = "服务器IP"
    # TURN_PORT = 8888  # UE5 coturn 默认端口是 8888
    # TURN_USER = "用户名"
    # TURN_PASSWORD = "密码"
```

### 环境变量配置

#### 1. 创建 `.env` 文件

```bash
# 复制示例配置
cp .env.example .env
```

#### 2. 编辑 `.env` 文件

```bash
# 服务端口（默认 8080）
PORT=8080

# TURN 配置（外网部署时取消注释）
# TURN 服务器地址
TURN_SERVER=你的服务器IP
# UE5 coturn 默认端口是 8888
TURN_PORT=8888
# 如果 TURN 需要认证，取消下面两行注释
# TURN_USER=用户名
# TURN_PASSWORD=密码
```

#### 3. 启动应用

```bash
python run.py
```

程序会自动加载 `.env` 文件中的环境变量。

#### 配置项说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `HOST` | 服务监听地址 | `0.0.0.0` |
| `PORT` | 服务端口 | `8080` |
| `TURN_SERVER` | TURN 服务器 IP/域名 | （空，不使用 TURN） |
| `TURN_PORT` | TURN 服务器端口 | `8888` |
| `TURN_USER` | TURN 用户名（可选） | （空） |
| `TURN_PASSWORD` | TURN 密码（可选） | （空） |

#### 4. 验证配置

```bash
# 查看加载的配置
python -c "from app.config import Config; print(Config.get_ice_servers())"
```

如果配置正确，会输出 ICE 服务器列表。

### 前端配置 (`web/public/index.html`)

```javascript
const iceServers = [
    { urls: 'stun:stun.l.google.com:19302' },
    // 外网部署时添加 TURN：
    // { urls: 'turn:你的服务器IP:3478?transport=udp' }
];
```

### 部署场景

| 场景 | ICE 配置 |
|------|---------|
| 本机测试 | 仅 STUN |
| 内网互联 | 仅 STUN |
| 外网服务器 + 内网客户端 | STUN + TURN |
| 外网服务器 + 外网客户端 | STUN + TURN |

### 使用 UE5 TURN 服务

UE5 内置 coturn TURN 服务器，默认端口 **8888**，无认证：

```bash
# .env 配置
TURN_SERVER=你的UE5服务器IP
TURN_PORT=8888
# 无需用户名密码（UE5 coturn 默认配置）
```

```python
# 或直接修改 app/config.py
TURN_SERVER = "你的UE5服务器IP"
TURN_PORT = 8888
```

## API

### WebSocket `/ws?session=<id>`

WebRTC 信令通道，用于视频流传输。

### REST API `/browse?session=<id>`

```bash
# 创建会话
curl -X POST "/browse?session=test" \
  -H "Content-Type: application/json" \
  -d '{"action":"create"}'

# 导航到 URL
curl -X POST "/browse?session=test" \
  -H "Content-Type: application/json" \
  -d '{"action":"navigate","url":"https://example.com"}'

# 执行 JavaScript
curl -X POST "/browse?session=test" \
  -H "Content-Type: application/json" \
  -d '{"action":"evaluate","script":"document.title"}'

# 关闭会话
curl -X POST "/browse?session=test" \
  -H "Content-Type: application/json" \
  -d '{"action":"close"}'
```

## 项目结构

```
browser-stream/
├── app/
│   ├── __init__.py
│   ├── config.py         # 配置文件
│   ├── main.py           # 服务器入口
│   ├── browser/          # 浏览器管理
│   │   └── manager.py
│   ├── handlers/         # HTTP/WebSocket 处理器
│   │   ├── http.py
│   │   └── websocket.py
│   └── webrtc/           # WebRTC 端连接
│       └── peer.py
├── web/
│   └── public/           # 前端文件
├── .env.example           # 环境变量示例
├── requirements.txt
└── run.py
```

## Docker

### Linux 服务器（推荐生产环境使用）

Linux 下 Docker 网络与宿主机直接打通，WebRTC 可正常工作。

```bash
# 安装 Docker（如需要）
curl -fsSL https://get.docker.com | sh

# 构建并运行
docker compose up --build -d

# 查看日志
docker compose logs -f

# 停止
docker compose down
```

**Docker 配置说明**：
- 默认使用 amd64 架构
- 服务端口：8080
- 包含 coturn TURN 服务器（端口 3478）
- TURN 用户名：`turnuser`，密码：`turnpassword`

### macOS/Windows（本地开发）

Docker Desktop 在 macOS 和 Windows 上有网络隔离限制。本地 WebRTC 测试建议**直接在宿主机运行**。

如必须使用 Docker，建议使用 Linux VM 或云服务器。

**注意**：在 macOS 或 Windows 上使用 Docker Desktop 时，WebRTC ICE 连接可能因 Docker 虚拟网络而失败。本地开发请使用直接安装方式。
