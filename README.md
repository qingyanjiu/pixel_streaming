# Browser Stream (Python Edition)

A server-side headless browser streaming application using WebRTC.

## Features

- Headless Chrome browser control via Playwright
- WebRTC-based screen streaming
- Browser navigation and script evaluation via REST API

## Tech Stack

- **Playwright** - Browser automation
- **aiohttp** - HTTP/WebSocket server
- **aiortc** - WebRTC peer connection

## Quick Start

### Prerequisites

- Python 3.10+
- Chromium or Chrome browser installed
- Run `playwright install chromium` to install browser

### Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### Run

```bash
python run.py
```

Open http://localhost:8080 in your browser.

## API

### WebSocket `/ws?session=<id>`

WebRTC signaling channel for video streaming.

### REST API `/browse?session=<id>`

```bash
# Create session
curl -X POST "/browse?session=test" \
  -H "Content-Type: application/json" \
  -d '{"action":"create"}'

# Navigate
curl -X POST "/browse?session=test" \
  -H "Content-Type: application/json" \
  -d '{"action":"navigate","url":"https://example.com"}'

# Evaluate JavaScript
curl -X POST "/browse?session=test" \
  -H "Content-Type: application/json" \
  -d '{"action":"evaluate","script":"document.title"}'

# Close session
curl -X POST "/browse?session=test" \
  -H "Content-Type: application/json" \
  -d '{"action":"close"}'
```

## Project Structure

```
browser-stream/
├── app/
│   ├── __init__.py
│   ├── main.py           # Server entry point
│   ├── browser/          # Browser management
│   │   └── manager.py
│   ├── handlers/         # HTTP/WebSocket handlers
│   │   ├── http.py
│   │   └── websocket.py
│   └── webrtc/           # WebRTC peer connection
│       └── peer.py
├── web/
│   └── public/           # Frontend files
├── requirements.txt
└── run.py
```
